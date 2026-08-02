"""Sync project-manifest.yaml to every supported AI platform directory."""

from __future__ import annotations

from pathlib import Path

from _engine.roots import lazy_root

CANONICAL_REL = ".github/project-manifest.yaml"

# (relative path, platform label for header)
MANIFEST_TARGETS: tuple[tuple[str, str], ...] = (
    (".github/project-manifest.yaml", "GitHub Copilot (canonical — edit here)"),
    (".claude/project-manifest.yaml", "Claude Code"),
    (".grok/project-manifest.yaml", "Grok Build"),
    (".gemini/project-manifest.yaml", "Google Gemini"),
    (".copilot/project-manifest.yaml", "GitHub Copilot (.copilot workspace)"),
    (".cursor/project-manifest.yaml", "Cursor IDE"),
    (".chatgpt/project-manifest.yaml", "ChatGPT / OpenAI (Codex, Agents)"),
)

SYNC_HINT = "python3 scripts/sync_manifests.py"


def extract_manifest_body(text: str) -> str:
    """Return YAML body from first non-comment, non-blank line onward."""
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            start = i
            break
    body = "\n".join(lines[start:]).rstrip() + "\n"
    return body


def platform_header(platform: str, *, canonical: bool = False) -> str:
    lines = [
        "# Project Manifest v1",
        "# Purpose: make prompts/agents portable across repositories and reduce token cost.",
        f"# Platform: {platform}",
    ]
    if canonical:
        lines.append(f"# Sync copies: {SYNC_HINT}")
    else:
        lines.append(f"# Canonical: {CANONICAL_REL} — refresh via {SYNC_HINT}")
    lines.append("")
    return "\n".join(lines)


def read_canonical_body(root: Path) -> str:
    """Prefer .github; fall back to any synced platform copy (e.g. deploy test targets)."""
    for rel, _ in MANIFEST_TARGETS:
        path = root / rel
        if path.is_file():
            return extract_manifest_body(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"No project manifest found under {root} "
        f"(expected one of: {', '.join(r for r, _ in MANIFEST_TARGETS)})"
    )


def sync_manifests(root: Path | None = None, *, dry_run: bool = False) -> list[str]:
    """Write platform manifests from canonical .github copy. Returns paths touched."""
    root = root or lazy_root()
    body = read_canonical_body(root)
    touched: list[str] = []

    for rel, platform in MANIFEST_TARGETS:
        dest = root / rel
        canonical = rel == CANONICAL_REL
        content = platform_header(platform, canonical=canonical) + body
        rel_str = str(Path(rel))
        if dest.is_file() and dest.read_text(encoding="utf-8") == content:
            continue
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        touched.append(rel_str)
    return touched


def manifest_search_paths(root: Path) -> list[Path]:
    """Ordered manifest locations for read fallback (first existing wins)."""
    return [root / rel for rel, _ in MANIFEST_TARGETS]


def find_manifest_path(root: Path) -> Path | None:
    """Return first existing manifest in canonical order (.github first).

    For Grok sessions, prefer find_grok_manifest_path instead.
    """
    for path in manifest_search_paths(root):
        if path.is_file():
            return path
    return None


def find_grok_manifest_path(root: Path) -> Path | None:
    """Prefer .grok/project-manifest.yaml (for Grok Build users) if present.

    Falls back to the standard search order. This allows Grok sessions
    on wave/fleet apps to use their platform-specific copy.
    """
    grok_path = root / ".grok/project-manifest.yaml"
    if grok_path.is_file():
        return grok_path
    return find_manifest_path(root)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    touched = sync_manifests(dry_run=args.dry_run)
    if args.dry_run:
        print(f"Would update {len(touched)} manifest(s)")
    else:
        print(f"Synced {len(touched)} manifest(s)")
    for rel in touched:
        print(f"  - {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())