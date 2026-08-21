"""Version resolution + comparison.

**SSOT:** the ``VERSION`` file (full product identity, e.g. ``1.9.5`` or ``1.9.0-pre.5``).

Three independent clocks (do not conflate them):

| Clock | Meaning | Where |
|-------|---------|--------|
| **host / CLI** | Package on PATH (`orchestrator` binary) | pip / uv tool / npm → Python |
| **template** | Surfaces this CLI would *deploy* | bundled wheel template, dev checkout, or ``ORCHESTRATOR_TEMPLATE_ROOT`` |
| **app lock** | What an *app repo* last installed | ``.orchestrator-version`` |

Hatch may stamp the wheel as **core only** ``X.Y.Z`` (see pyproject); full identity
always lives in ``VERSION`` / deploy stamp. CLI identity prefers the full
``VERSION`` when available so pre-releases are not collapsed.
"""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import Any

from .template_root import dev_repo_root, is_bundled, template_root


def core_version(v: str | None) -> str:
    """MAJOR.MINOR.PATCH only (strip leading v, pre-release, build)."""
    raw = (v or "").strip().lstrip("v")
    if not raw:
        return ""
    return raw.split("-", 1)[0].split("+", 1)[0]


def normalize_version(v: str | None) -> str:
    """Strip whitespace and leading ``v``; keep pre-release suffix."""
    return (v or "").strip().lstrip("v")


def _parse(v: str) -> tuple[int, int, int]:
    """Core MAJOR.MINOR.PATCH only (strips pre-release / build). Legacy helper."""
    parts = core_version(v).split(".")[:3]
    nums = [int(p) for p in parts if p.isdigit()]
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2])


def _pep440(v: str):
    """Parse versions including pre-release tags (1.9.0-pre.5 → comparable)."""
    from packaging.version import Version

    return Version(normalize_version(v))


def versions_equal(a: str | None, b: str | None, *, core_ok: bool = True) -> bool:
    """True if versions match fully.

    When *core_ok*, two pure-core strings with the same X.Y.Z also match
    (hatch wheel vs VERSION on a final release). A pre-release never equals
    bare core (``1.9.0-pre.5`` ≠ ``1.9.0``).
    """
    na, nb = normalize_version(a), normalize_version(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if not core_ok:
        return False
    ca, cb = core_version(na), core_version(nb)
    if ca != cb:
        return False
    # Both pure core (no pre/build suffix)
    return na == ca and nb == cb


def template_version() -> str:
    """The template/release version from the VERSION file (SSOT)."""
    vfile = template_root() / "VERSION"
    if vfile.is_file():
        text = vfile.read_text(encoding="utf-8").strip().splitlines()
        if text:
            return normalize_version(text[0])
    raise RuntimeError("VERSION file not found")


def package_metadata_version() -> str | None:
    """Installed distribution version from importlib.metadata, or None."""
    try:
        return normalize_version(metadata.version("orchestrator"))
    except metadata.PackageNotFoundError:
        return None


def cli_version() -> str:
    """Version identity for this CLI process (product identity, not hatch core alone).

    Priority:
    1. Dev checkout → **VERSION file**
    2. Bundled / installed → **VERSION** from template when present (full identity);
       fall back to package metadata
    3. Package metadata only
    """
    meta = package_metadata_version()
    if not is_bundled() and dev_repo_root() is not None:
        try:
            return template_version()
        except RuntimeError:
            if meta:
                return meta
            raise
    try:
        tmpl = template_version()
    except RuntimeError:
        tmpl = None
    if tmpl:
        # Prefer full VERSION identity; meta is often core-only via hatch pattern
        if not meta or meta == tmpl or core_version(meta) == core_version(tmpl):
            return tmpl
        # Divergent metadata wins only if strictly newer (weird reinstall)
        if is_newer(meta, tmpl):
            return meta
        return tmpl
    return meta or "0.0.0"


def app_lock_version(target: Path | None = None) -> str | None:
    """``.orchestrator-version`` lock in *target* (default cwd), if present."""
    from .lock import read_lock

    lock = read_lock(target or Path.cwd())
    if not lock:
        return None
    ver = lock.get("version")
    return normalize_version(str(ver)) if ver else None


def app_lock_cli_version(target: Path | None = None) -> str | None:
    """CLI version recorded at install time (may lag current host)."""
    from .lock import read_lock

    lock = read_lock(target or Path.cwd())
    if not lock:
        return None
    ver = lock.get("cli_version")
    return normalize_version(str(ver)) if ver else None


def runtime_mode() -> str:
    """Human mode label for version command."""
    if is_bundled():
        return "installed"
    if dev_repo_root() is not None:
        return "dev checkout"
    return "unknown"


def is_template_source_tree(target: Path | None = None) -> bool:
    """True when *target* is the orchestrator template monorepo (not a consumer app).

    Must work when the running CLI is a **bundled** install whose
    ``template_root()`` is inside site-packages — equality with template_root
    alone is not enough.
    """
    t = (target or Path.cwd()).resolve()
    try:
        if t == template_root().resolve():
            return True
    except Exception:
        pass
    # Source checkout fingerprints (not present on consumer apps)
    if (t / "scripts" / "deploy-bundle.yaml").is_file() and (
        t / "src" / "orchestrator_cli"
    ).is_dir():
        return True
    if (t / "pyproject.toml").is_file() and (t / "VERSION").is_file():
        try:
            text = (t / "pyproject.toml").read_text(encoding="utf-8")
            if 'name = "orchestrator"' in text and (t / "src" / "orchestrator_cli").is_dir():
                return True
        except OSError:
            pass
    return False


def version_report(target: Path | None = None) -> dict[str, Any]:
    """Structured multi-clock version report for CLI / tests / agents."""
    target = (target or Path.cwd()).resolve()
    mode = runtime_mode()
    try:
        tmpl = template_version()
    except RuntimeError:
        tmpl = None
    cli = cli_version()
    meta = package_metadata_version()
    app = app_lock_version(target)
    app_cli = app_lock_cli_version(target)
    source_tree = is_template_source_tree(target)

    notes: list[str] = []
    actions: list[str] = []

    host_aligned = bool(tmpl and versions_equal(cli, tmpl, core_ok=True))
    if meta and tmpl and core_version(meta) == core_version(tmpl) and meta != tmpl:
        notes.append(
            f"package metadata {meta!r} is hatch core-only; "
            f"product identity uses VERSION={tmpl}"
        )
    if mode == "dev checkout" and meta and tmpl and not versions_equal(meta, tmpl, core_ok=True):
        notes.append(
            f"pip metadata was {meta} (stale); CLI identity uses VERSION={tmpl} — "
            f"refresh: orchestrator self-upgrade --yes  or  bash scripts/install.sh --uv-tool"
        )
        actions.append("orchestrator self-upgrade --yes")

    app_status = "n/a"
    if source_tree:
        app_status = "template_source"
        notes.append(
            "cwd is orchestrator template source — app init/upgrade N/A "
            "(host package is separate from this git tree)"
        )
    elif app is None:
        app_status = "not_installed"
        if (target / ".grok").is_dir() or (target / "chains").is_dir():
            notes.append(
                "no .orchestrator-version lock — run: orchestrator init . --no-pr"
            )
            actions.append(f"orchestrator init {target} --no-pr")
    elif tmpl and is_newer(tmpl, app):
        app_status = "behind"
        notes.append(
            f"app lock {app} is behind template {tmpl} — "
            f"upgrade app (not host): orchestrator upgrade {target} "
            f"--from-github v{tmpl} --yes --no-pr"
        )
        actions.append(
            f"orchestrator upgrade {target} --from-github v{tmpl} --yes --no-pr"
        )
    elif tmpl and is_newer(app, tmpl):
        app_status = "ahead"
        notes.append(
            f"app lock {app} is ahead of this CLI's template {tmpl} — "
            f"refresh host: orchestrator self-upgrade --to {app} --yes"
        )
        actions.append(f"orchestrator self-upgrade --to {app} --yes")
    else:
        app_status = "current"
        if app and app_cli and not versions_equal(app_cli, cli, core_ok=True):
            notes.append(
                f"app was installed with host CLI {app_cli}; current host is {cli} "
                f"(ok if you self-upgraded later)"
            )

    if mode == "installed" and meta and tmpl and not versions_equal(meta, tmpl, core_ok=True):
        notes.append(
            f"host package metadata {meta} != template {tmpl} — "
            f"orchestrator self-upgrade --to {tmpl} --yes"
        )
        actions.append(f"orchestrator self-upgrade --to {tmpl} --yes")

    # Overall: host ok + (app n/a|current|template_source)
    overall = host_aligned and app_status in (
        "n/a",
        "current",
        "template_source",
    )

    return {
        "ssot": "VERSION",
        "cli": cli,
        "template": tmpl,
        "mode": mode,
        "package_metadata": meta,
        "package_core": core_version(meta) if meta else None,
        "app_lock": app,
        "app_cli_at_install": app_cli,
        "app_status": app_status,
        "host_aligned": host_aligned,
        "is_template_source": source_tree,
        "target": str(target),
        "notes": notes,
        "actions": actions,
        "aligned": overall,
        # Back-compat keys used by older tests / callers
        "version": cli,
    }


def format_version_report(rep: dict[str, Any]) -> str:
    """Human multi-line matrix (token-cheap)."""
    lines = [
        f"orchestrator {rep.get('cli') or '?'} "
        f"(template {rep.get('template') or '?'}, {rep.get('mode') or '?'})"
    ]
    lines.append(
        f"  host:     {rep.get('cli') or '?'}  "
        f"meta={rep.get('package_metadata') or '—'}  "
        f"aligned={'yes' if rep.get('host_aligned') else 'no'}"
    )
    lines.append(f"  template: {rep.get('template') or '?'}  (SSOT=VERSION)")
    app = rep.get("app_lock")
    st = rep.get("app_status") or "n/a"
    if rep.get("is_template_source"):
        lines.append("  app:      —  (template source tree; not an app)")
    elif app:
        lines.append(
            f"  app:      {app}  ({st})  "
            f"installed_with_cli={rep.get('app_cli_at_install') or '—'}"
        )
    else:
        lines.append(f"  app:      —  ({st})")
    lines.append(f"  target:   {rep.get('target')}")
    for note in rep.get("notes") or []:
        lines.append(f"  note: {note}")
    for act in rep.get("actions") or []:
        lines.append(f"  → {act}")
    return "\n".join(lines)


def is_newer(candidate: str, current: str) -> bool:
    """True if candidate is strictly newer than current (PEP 440 / pre-release aware).

    Handles template stamps like ``1.9.0-pre.3`` vs ``1.9.0-pre.5`` (core-only
    compare treated both as 1.9.0 and blocked upgrades).
    """
    try:
        return _pep440(candidate) > _pep440(current)
    except Exception:
        return _parse(candidate) > _parse(current)


# Back-compat aliases used elsewhere
_normalize = normalize_version
_core = core_version
