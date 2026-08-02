"""Project-manifest identity check — not still the orchestrator template.

Any model that reads project-manifest.yaml must verify the file describes *this*
repo (name, stack, runtime), not the stock "Project Template" defaults left after
deploy. Orchestrator source repo is allowed to keep template values.

Exit-oriented statuses:
  ok               — customized or legitimate template source
  warn             — partial mismatch / incomplete customization
  template_residue — still looks like the orchestrator template (non-source apps)
  missing          — no manifest found
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

MANIFEST_CANDIDATES = (
    ".grok/project-manifest.yaml",
    ".github/project-manifest.yaml",
    ".claude/project-manifest.yaml",
    ".copilot/project-manifest.yaml",
    ".cursor/project-manifest.yaml",
    ".gemini/project-manifest.yaml",
)

TEMPLATE_NAMES = frozenset(
    {
        "project template",
        "orchestrator template",
        "reusable orchestrator template",
    }
)

TEMPLATE_DESCRIPTION_SNIPPETS = (
    "reusable orchestrator template",
    "fast start-to-beta delivery",
    "manifest-first ai template",
)

STACK_SIGNAL_TO_FRAMEWORK = {
    "laravel": "laravel",
    "django": "django",
    "fastapi": "fastapi",
    "flask": "flask",
    "nextjs": "nextjs",
    "nuxt": "nuxt",
    "astro": "astro",
    "go": "go",
}


def find_manifest_path(root: Path) -> Path | None:
    for rel in MANIFEST_CANDIDATES:
        path = root / rel
        if path.is_file():
            return path
    return None


def is_orchestrator_source_repo(root: Path) -> bool:
    """True when this tree is the orchestrator template source (not a deployed app)."""
    slug = root.name.lower()
    if slug != "orchestrator":
        return False
    return (root / "scripts" / "deploy_grok_to_project.py").is_file()


def detect_stack_signals(root: Path) -> list[str]:
    """Return ordered stack signals inferred from repo files (not the manifest)."""
    signals: list[str] = []
    if (root / "artisan").is_file() and (root / "composer.json").is_file():
        signals.append("laravel")
    if (root / "manage.py").is_file():
        signals.append("django")
    if (root / "go.mod").is_file():
        signals.append("go")
    pkg_path = root / "package.json"
    if pkg_path.is_file():
        try:
            pkg = pkg_path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            pkg = ""
        if "next" in pkg or '"next"' in pkg:
            signals.append("nextjs")
        if "nuxt" in pkg:
            signals.append("nuxt")
        if "astro" in pkg:
            signals.append("astro")
    # Python API frameworks without manage.py
    for marker, name in (
        ("pyproject.toml", None),
        ("requirements.txt", None),
    ):
        path = root / marker
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        if "fastapi" in text and "fastapi" not in signals:
            signals.append("fastapi")
        if "flask" in text and "flask" not in signals:
            signals.append("flask")
        if name and name not in signals:
            signals.append(name)
    # de-dupe preserve order
    return list(dict.fromkeys(signals))


def _field(text: str, key: str) -> str | None:
    # Match project.name / framework / language style keys at any indent
    pat = re.compile(
        rf"^\s*{re.escape(key)}:\s*[\"']?([^\"'#\n]+)[\"']?",
        re.MULTILINE,
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def _bool_field(text: str, key: str) -> bool | None:
    raw = _field(text, key)
    if raw is None:
        return None
    low = raw.lower()
    if low in {"true", "yes", "1"}:
        return True
    if low in {"false", "no", "0"}:
        return False
    return None


def parse_manifest_identity_fields(manifest_text: str) -> dict[str, Any]:
    return {
        "project_name": _field(manifest_text, "name") or "",
        "description": _field(manifest_text, "description") or "",
        "framework": (_field(manifest_text, "framework") or "generic").lower(),
        "language": (_field(manifest_text, "language") or "generic").lower(),
        "uses_database": _bool_field(manifest_text, "uses_database"),
        "database_engine": (_field(manifest_text, "database_engine") or "none").lower(),
        "environment_manager": (
            _field(manifest_text, "environment_manager") or "local"
        ).lower(),
    }


def check_manifest_identity(root: Path) -> dict[str, Any]:
    """Evaluate whether the project-manifest matches the repo it lives in."""
    root = root.resolve()
    path = find_manifest_path(root)
    result: dict[str, Any] = {
        "status": "missing",
        "ok": False,
        "is_orchestrator_source": is_orchestrator_source_repo(root),
        "repo_slug": root.name,
        "manifest_path": None,
        "project_name": None,
        "framework": None,
        "language": None,
        "detected_stack": detect_stack_signals(root),
        "issues": [],
        "recommendations": [],
        "briefing_line": "",
    }

    if path is None:
        result["issues"].append("no project-manifest.yaml found under platform dirs")
        result["recommendations"].append(
            "run orchestrator init / upgrade, or copy a platform manifest and customize project + stack"
        )
        result["briefing_line"] = (
            "Manifest identity: MISSING — no project-manifest.yaml (cannot confirm project)"
        )
        return result

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result["issues"].append(f"cannot read manifest: {exc}")
        result["briefing_line"] = f"Manifest identity: ERROR — {exc}"
        return result

    fields = parse_manifest_identity_fields(text)
    result["manifest_path"] = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    result["project_name"] = fields["project_name"]
    result["framework"] = fields["framework"]
    result["language"] = fields["language"]
    result["uses_database"] = fields["uses_database"]
    result["database_engine"] = fields["database_engine"]
    result["environment_manager"] = fields["environment_manager"]

    if result["is_orchestrator_source"]:
        result["status"] = "ok"
        result["ok"] = True
        result["briefing_line"] = (
            "Manifest identity: OK (orchestrator template source — stock values expected)"
        )
        return result

    issues: list[str] = []
    recs: list[str] = []

    name_low = (fields["project_name"] or "").strip().lower()
    desc_low = (fields["description"] or "").strip().lower()

    if not name_low or name_low in TEMPLATE_NAMES:
        issues.append(
            f'project.name is still template placeholder ({fields["project_name"]!r})'
        )
        recs.append(
            f'set project.name to this app (dir slug often "{root.name}") in all platform manifests'
        )

    for snippet in TEMPLATE_DESCRIPTION_SNIPPETS:
        if snippet in desc_low:
            issues.append("project.description still describes the orchestrator template")
            recs.append("rewrite project.description for this application")
            break

    detected = result["detected_stack"]
    fw = fields["framework"]
    lang = fields["language"]

    if detected and fw in {"generic", "", "none"}:
        expected = STACK_SIGNAL_TO_FRAMEWORK.get(detected[0], detected[0])
        issues.append(
            f"stack.framework is {fw!r} but repo signals look like {detected[0]} "
            f"(expected framework closer to {expected!r})"
        )
        recs.append(
            f"set stack.framework/language (and database_*) for {detected[0]} in project-manifest.yaml"
        )

    if "laravel" in detected:
        if fields["uses_database"] is False:
            issues.append("Laravel signals present but stack.uses_database is false")
            recs.append("set uses_database: true and database_engine for this app")
        if fields["environment_manager"] == "local" and (root / ".ddev" / "config.yaml").is_file():
            issues.append(
                "Laravel app has .ddev/ but runtime.environment_manager is still local"
            )
            recs.append('set runtime.environment_manager: "ddev"')

    # Directory slug vs customized name — soft signal only when name still orchestrator
    if name_low == "orchestrator" and root.name.lower() != "orchestrator":
        issues.append(
            f'project.name is "orchestrator" but repo directory is {root.name!r}'
        )
        recs.append("rename project.name to the real app after template deploy")

    if not issues:
        result["status"] = "ok"
        result["ok"] = True
        result["briefing_line"] = (
            f"Manifest identity: OK — {fields['project_name']!r} "
            f"(framework={fw}, detected={detected or ['none']})"
        )
        return result

    # Hard = still stock template or generic stack while app signals exist
    hard = (
        (not name_low or name_low in TEMPLATE_NAMES)
        or any("describes the orchestrator template" in i for i in issues)
        or (bool(detected) and fw == "generic")
        or (name_low == "orchestrator" and root.name.lower() != "orchestrator")
    )

    result["issues"] = issues
    result["recommendations"] = list(dict.fromkeys(recs))
    if hard:
        result["status"] = "template_residue"
        result["ok"] = False
        result["briefing_line"] = (
            "Manifest identity: TEMPLATE_RESIDUE — still looks like orchestrator template; "
            "customize project-manifest before trusting stack/runtime"
        )
    else:
        result["status"] = "warn"
        result["ok"] = False
        result["briefing_line"] = (
            "Manifest identity: WARN — partial mismatch between manifest and repo signals"
        )
    return result


def format_text_report(result: dict[str, Any]) -> str:
    lines = [
        f"status={result.get('status')}",
        f"ok={str(result.get('ok')).lower()}",
        f"is_orchestrator_source={str(result.get('is_orchestrator_source')).lower()}",
        f"repo_slug={result.get('repo_slug')}",
        f"manifest_path={result.get('manifest_path') or 'none'}",
        f"project_name={result.get('project_name') or 'none'}",
        f"framework={result.get('framework') or 'none'}",
        f"language={result.get('language') or 'none'}",
        f"detected_stack={','.join(result.get('detected_stack') or []) or 'none'}",
        f"briefing_line={result.get('briefing_line') or ''}",
    ]
    issues = result.get("issues") or []
    recs = result.get("recommendations") or []
    if issues:
        lines.append("issues:")
        for i in issues:
            lines.append(f"  - {i}")
    if recs:
        lines.append("recommendations:")
        for r in recs:
            lines.append(f"  - {r}")
    return "\n".join(lines) + "\n"
