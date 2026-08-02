#!/usr/bin/env python3
"""
scan.py — Collect project discovery information for the acquire-codebase-knowledge skill.
Run from the project root directory.

Multi-language manifest detection, project-local stack inference, CI/CD markers,
container config, and tree overview. Runs in whichever repo it is installed in.

Usage: python3 scan.py [OPTIONS]

Options:
  --output FILE   Write output to FILE instead of stdout
  --help          Show this message and exit

Exit codes:
  0  Success
  1  Usage error
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import re

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

TREE_LIMIT = 200
TREE_MAX_DEPTH = 3
TODO_LIMIT = 60
MANIFEST_PREVIEW_LINES = 80
RECENT_COMMITS_LIMIT = 20

# Standard build artifacts + common large/generated dirs
EXCLUDE_DIRS = {
    "node_modules", ".git", "dist", "build", "out", ".next", ".nuxt",
    "__pycache__", ".venv", "venv", ".tox", "target", "vendor",
    "coverage", ".nyc_output", "generated", ".cache", ".turbo",
    ".yarn", ".pnp", "bin", "obj",
    "htmlcov",
    # Optional large dirs — skip deep walk; still documented at high level
    "backup", "outputs", "reports",
}

MANIFESTS = [
    # JavaScript/Node.js
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
    "deno.json", "deno.jsonc",
    # Python
    "requirements.txt", "Pipfile", "Pipfile.lock", "pyproject.toml", "setup.py", "setup.cfg",
    "poetry.lock", "pdm.lock", "uv.lock",
    # Go
    "go.mod", "go.sum",
    # Rust
    "Cargo.toml", "Cargo.lock",
    # Java/Kotlin
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties",
    # PHP/Composer
    "composer.json", "composer.lock",
    # Ruby
    "Gemfile", "Gemfile.lock", "*.gemspec",
    # Elixir
    "mix.exs", "mix.lock",
    # Dart/Flutter
    "pubspec.yaml", "pubspec.lock",
    # .NET/C#
    "*.csproj", "*.sln", "*.slnx", "global.json", "packages.config",
    # Swift
    "Package.swift", "Package.resolved",
    # Scala
    "build.sbt", "scala-cli.yml",
    # Haskell
    "*.cabal", "stack.yaml", "cabal.project", "cabal.project.local",
    # OCaml
    "dune-project", "opam", "opam.lock",
    # Nim
    "*.nimble", "nim.cfg",
    # Crystal
    "shard.yml", "shard.lock",
    # R
    "DESCRIPTION", "renv.lock",
    # Julia
    "Project.toml", "Manifest.toml",
    # Build / container systems
    "CMakeLists.txt", "Makefile", "GNUmakefile",
    "SConstruct", "build.xml",
    "BUILD", "BUILD.bazel", "WORKSPACE", "bazel.lock",
    "justfile", ".justfile", "Taskfile.yml",
    "tox.ini", "Vagrantfile",
    # Docker / compose
    "Dockerfile", "Dockerfile.prod", "Dockerfile.hardened",
    "docker-compose.yml", "docker-compose.prod.yml", "docker-compose.hardened.yml",
    "docker-compose.*.yml",
    # DDEV
    ".ddev/config.yaml", "ddev-config.yaml",
    # Testing / CI
    "pytest.ini", ".coveragerc", "phpunit.xml", "pest.xml",
    # Orchestrator / manifest - .grok first for Grok sessions on wave/fleet
    ".grok/project-manifest.yaml",
    ".claude/project-manifest.yaml", ".github/project-manifest.yaml",
    "chains/registry.yaml", "CHAIN.md",
]

ENTRY_CANDIDATES = [
    # JavaScript/Node.js/TypeScript
    "src/index.ts", "src/index.js", "src/index.mjs",
    "src/main.ts", "src/main.js", "src/main.py",
    "src/app.ts", "src/app.js",
    "src/server.ts", "src/server.js",
    "index.ts", "index.js", "app.ts", "app.js",
    "lib/index.ts", "lib/index.js",
    # Go
    "main.go", "cmd/main.go",
    # Python
    "main.py", "app.py", "server.py", "run.py", "cli.py",
    "src/main.py", "src/__main__.py",
    # PHP / Laravel
    "public/index.php", "index.php", "artisan",
    # Orchestrator
    "CLAUDE.md", "LOOP.md",
]


def run_command(cmd: List[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"ERROR running {' '.join(cmd)}: {e}"


def get_tree(root: Path, max_depth: int = TREE_MAX_DEPTH, limit: int = TREE_LIMIT) -> List[str]:
    lines = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts)
        if depth > max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith('.')]
        if count >= limit:
            break
        indent = "  " * depth
        lines.append(f"{indent}{rel.name or '.'}/")
        count += 1
        for f in sorted(filenames)[:20]:
            if count >= limit:
                break
            lines.append(f"{indent}  {f}")
            count += 1
    if count >= limit:
        lines.append(f"... (truncated at {limit} entries)")
    return lines


def find_manifests(root: Path) -> List[Path]:
    found = []
    for name in MANIFESTS:
        if "*" in name:
            for p in root.rglob(name):
                if not any(ex in p.parts for ex in EXCLUDE_DIRS):
                    found.append(p)
        else:
            p = root / name
            if p.exists():
                found.append(p)
    return sorted(set(found))[:30]


MANIFEST_PATHS = [
    ".grok/project-manifest.yaml",  # Grok preference for wave/fleet apps
    ".claude/project-manifest.yaml",
    ".github/project-manifest.yaml",
]


def read_project_manifest(root: Path) -> Tuple[Optional[dict], Optional[str]]:
    for rel in MANIFEST_PATHS:
        p = root / rel
        if not p.exists():
            continue
        text = p.read_text(errors="ignore")
        if yaml is None:
            return None, rel
        try:
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                return data, rel
        except Exception:
            return None, rel
    return None, None


def detect_stack_signals(root: Path) -> List[str]:
    """Infer stack from files present in the installed project (not template defaults)."""
    signals: List[str] = []

    checks: List[Tuple[str, str]] = [
        ("composer.json", "PHP (Composer)"),
        ("artisan", "Laravel (artisan present)"),
        ("package.json", "Node.js / JavaScript"),
        ("requirements.txt", "Python (pip)"),
        ("pyproject.toml", "Python (pyproject)"),
        ("go.mod", "Go"),
        ("Cargo.toml", "Rust"),
        ("pom.xml", "Java (Maven)"),
        ("build.gradle", "Java/Kotlin (Gradle)"),
        ("build.gradle.kts", "Kotlin (Gradle)"),
        ("Gemfile", "Ruby"),
        ("mix.exs", "Elixir"),
        ("pubspec.yaml", "Dart / Flutter"),
        ("Dockerfile", "Docker"),
        (".ddev/config.yaml", "DDEV local runtime"),
        ("chains/registry.yaml", "Orchestrator chains"),
        ("CHAIN.md", "Orchestrator chain registry"),
        ("LOOP.md", "Orchestrator loops"),
        ("pest.xml", "PHP testing (Pest)"),
        ("phpunit.xml", "PHP testing (PHPUnit)"),
        ("pytest.ini", "Python testing (pytest)"),
    ]

    for rel, label in checks:
        if (root / rel).exists():
            signals.append(f"FOUND {rel} -> {label}")

    composer = root / "composer.json"
    if composer.exists():
        text = composer.read_text(errors="ignore").lower()
        if "laravel/framework" in text:
            signals.append("composer.json lists laravel/framework -> Laravel")
        if "filament/filament" in text:
            signals.append("composer.json lists filament/filament -> Filament")

    package = root / "package.json"
    if package.exists():
        text = package.read_text(errors="ignore").lower()
        for dep, fw in [
            ('"next"', "Next.js"),
            ('"nuxt"', "Nuxt.js"),
            ('"react"', "React"),
            ('"vue"', "Vue"),
            ('"@nestjs/core"', "NestJS"),
        ]:
            if dep in text:
                signals.append(f"package.json dependency {dep} -> {fw}")

    reqs = root / "requirements.txt"
    if reqs.exists():
        text = reqs.read_text(errors="ignore").lower()
        for pkg, fw in [
            ("fastapi", "FastAPI"),
            ("flask", "Flask"),
            ("django", "Django"),
        ]:
            if pkg in text:
                signals.append(f"requirements.txt mentions {pkg} -> {fw}")

    if not signals:
        signals.append("No strong stack signals — inspect tree + README; use stack-detection.md")

    return signals


def format_detected_stack(root: Path) -> List[str]:
    lines = ["=== DETECTED STACK (installed project — do not assume other repos) ==="]
    manifest, manifest_path = read_project_manifest(root)
    if manifest_path:
        lines.append(f"Project manifest: {manifest_path}")
        if manifest:
            stack = manifest.get("stack") or {}
            runtime = manifest.get("runtime") or {}
            if isinstance(stack, dict):
                for key in ("framework", "language", "database_engine", "uses_database"):
                    if key in stack:
                        lines.append(f"  manifest.stack.{key}: {stack[key]}")
            if isinstance(runtime, dict):
                for key in ("environment_manager", "test_command", "start_command"):
                    if key in runtime and runtime[key]:
                        lines.append(f"  manifest.runtime.{key}: {runtime[key]}")
        elif yaml is None:
            lines.append("  (install PyYAML for parsed manifest; raw file still in MANIFESTS section)")
    else:
        lines.append("Project manifest: not found (derive stack from files below)")

    lines.append("")
    lines.append("File-based signals:")
    lines.extend(f"  - {s}" for s in detect_stack_signals(root))
    lines.append("")
    return lines


def find_todos(root: Path, limit: int = TODO_LIMIT) -> List[str]:
    todos = []
    pattern = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE)
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        if any(ex in rel.parts for ex in EXCLUDE_DIRS):
            dirnames[:] = []
            continue
        for fname in filenames:
            if not fname.endswith(('.py', '.php', '.js', '.ts', '.md', '.sql', '.yml', '.yaml', '.go', '.rs')):
                continue
            if len(todos) >= limit:
                break
            try:
                with open(Path(dirpath) / fname, 'r', errors='ignore') as fh:
                    for i, line in enumerate(fh, 1):
                        if pattern.search(line):
                            todos.append(f"{rel / fname}:{i}: {line.strip()[:120]}")
                            if len(todos) >= limit:
                                break
            except Exception:
                pass
    return todos


FRESHNESS_REL = "docs/codebase/.codebase-freshness.txt"


def write_freshness_marker(
    root: Path,
    output_path: Path,
    generated: str,
    stack_lines: List[str],
) -> Path:
    """Write a small lean-spine file agents may Read in cache-efficient mode."""
    full_line_count = 0
    if output_path.is_file():
        full_line_count = len(output_path.read_text(errors="ignore").splitlines())

    manifest, manifest_path = read_project_manifest(root)
    stale_days = 14
    if manifest and isinstance(manifest.get("token_policy"), dict):
        stale_days = manifest["token_policy"].get("cache_stale_days", stale_days)

    lines = [
        "# Codebase freshness (lean spine — cache-efficient / load-cache / standup only)",
        "# FORBIDDEN in lean mode: Read docs/codebase/.codebase-scan.txt (full scan artifact).",
        f"Generated: {generated}",
        f"Full scan artifact: docs/codebase/.codebase-scan.txt ({full_line_count} lines)",
        f"Full scan for: /acquire-codebase-knowledge, /read-codebase, /chain cache-rebuild only",
        f"Cache stale after: {stale_days} days (manifest token_policy.cache_stale_days)",
        "",
        "=== DETECTED STACK (summary) ===",
    ]
    for line in stack_lines:
        if line.startswith("==="):
            continue
        lines.append(line)

    freshness_path = root / FRESHNESS_REL
    freshness_path.parent.mkdir(parents=True, exist_ok=True)
    freshness_path.write_text("\n".join(lines).rstrip() + "\n")
    return freshness_path


def main():
    parser = argparse.ArgumentParser(
        description="Codebase scanner for acquire-codebase-knowledge (stack detection + tree)"
    )
    parser.add_argument("--output", "-o", type=str, default=None, help="Write output to this file")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    generated = subprocess.getoutput("date -u +%Y-%m-%dT%H:%M:%SZ")
    out_lines = []
    out_lines.append(f"Codebase Scan — {root}")
    out_lines.append(f"Generated: {generated}")
    out_lines.append("")

    stack_lines = format_detected_stack(root)
    out_lines.extend(stack_lines)

    out_lines.append("=== TREE (top levels, standard excludes) ===")
    out_lines.extend(get_tree(root))
    out_lines.append("")

    out_lines.append("=== MANIFESTS & CONFIGS ===")
    for m in find_manifests(root):
        try:
            text = m.read_text(errors='ignore')[:MANIFEST_PREVIEW_LINES * 10]
            out_lines.append(f"--- {m.relative_to(root)} ---")
            out_lines.append(text)
            out_lines.append("")
        except Exception as e:
            out_lines.append(f"--- {m} (error: {e}) ---")

    out_lines.append("=== KEY ENTRYPOINT CANDIDATES (checked) ===")
    for cand in ENTRY_CANDIDATES:
        p = root / cand
        if p.exists():
            out_lines.append(f"FOUND: {cand}")

    out_lines.append("")
    out_lines.append("=== RECENT COMMITS (churn signals) ===")
    log = run_command(["git", "log", "--oneline", f"-{RECENT_COMMITS_LIMIT}"], root)
    out_lines.append(log[:2000])

    out_lines.append("")
    out_lines.append("=== TODO/FIXME/HACK markers (first N in source) ===")
    for t in find_todos(root):
        out_lines.append(t)

    out_lines.append("")
    out_lines.append("=== DOCKER / COMPOSE / DDEV ===")
    for f in [
        "Dockerfile", "Dockerfile.hardened", "docker-compose.yml",
        "docker-compose.hardened.yml", "docker-compose.prod.yml", ".ddev/config.yaml",
    ]:
        p = root / f
        if p.exists():
            out_lines.append(f"--- {f} (head) ---")
            out_lines.append(p.read_text(errors='ignore')[:1500])
            out_lines.append("")

    out_lines.append("")
    out_lines.append("=== CI/CD WORKFLOWS ===")
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for wf in sorted(workflows.glob("*.yml"))[:10]:
            out_lines.append(f"--- {wf.relative_to(root)} (head) ---")
            out_lines.append(wf.read_text(errors='ignore')[:800])
            out_lines.append("")

    result = "\n".join(out_lines)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result)
        freshness_path = write_freshness_marker(root, output_path, generated, stack_lines)
        print(f"Scan written to {args.output}")
        print(f"Freshness marker written to {freshness_path.relative_to(root)}")
    else:
        print(result)


if __name__ == "__main__":
    main()