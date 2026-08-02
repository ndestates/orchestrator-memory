"""Path sandbox — confine reads and script execution to PROJECT_ROOT."""

from __future__ import annotations

from pathlib import Path

ALLOWED_READ_PREFIXES = (
    "docs/codebase",
    "TODO",
    ".grok",
    "chains",
    "patterns",
    "reports",
    "reports/vault",
    "scripts",
    ".github",
    ".claude",
    "wiki",
    "raw",
)

ALLOWED_READ_FILES = (
    "CHAIN.md",
    "LOOP.md",
    "STATE.md",
    "loop-budget.md",
    "loop-run-log.md",
    "CLAUDE.md",
    "IMPLEMENTATION_SUMMARY.md",
    "BRANCH_ANALYSIS.md",
)

ALLOWED_AUDIT_SCRIPTS = {
    "chain": "scripts/chain-audit.sh",
    "loop": "scripts/loop-audit.sh",
    "alignment": "scripts/check_name_alignment.py",
    "wiki": "scripts/wiki_lint_check.py",
}


class SandboxError(PermissionError):
    """Raised when a path or operation is outside the sandbox."""


def _resolve_under_root(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise SandboxError(f"Path escapes PROJECT_ROOT: {relative}") from exc
    return candidate


def assert_readable(root: Path, relative: str) -> Path:
    path = _resolve_under_root(root, relative)
    rel_posix = path.relative_to(root.resolve()).as_posix()

    if rel_posix in ALLOWED_READ_FILES:
        return path

    for prefix in ALLOWED_READ_PREFIXES:
        if rel_posix == prefix or rel_posix.startswith(prefix + "/"):
            return path

    raise SandboxError(f"Read not allowed: {relative}")


def is_untrusted_read_path(relative: str) -> bool:
    """True when MCP should soft-filter content before returning to the model."""
    try:
        import sys

        scripts = Path(__file__).resolve().parents[3] / "scripts"
        if scripts.is_dir() and str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from scripts._engine.untrusted_text import is_untrusted_read_path as _check

        return _check(relative)
    except ImportError:
        rel = relative.lstrip("./").replace("\\", "/")
        return rel.startswith("TODO") or rel.startswith("reports") or rel in {
            "STATE.md",
            "VISION.md",
            "loop-run-log.md",
        }


def read_bounded(root: Path, relative: str, max_bytes: int) -> str:
    path = assert_readable(root, relative)
    if not path.is_file():
        raise FileNotFoundError(relative)
    data = path.read_bytes()
    if len(data) > max_bytes:
        text = data[:max_bytes].decode("utf-8", errors="replace")
        text = text + f"\n\n[truncated at {max_bytes} bytes]"
    else:
        text = data.decode("utf-8", errors="replace")
    if is_untrusted_read_path(relative):
        try:
            import sys

            scripts = root / "scripts"
            if scripts.is_dir() and str(scripts) not in sys.path:
                sys.path.insert(0, str(scripts))
            from scripts._engine.untrusted_text import safe_for_ai

            pack = safe_for_ai(text, source=relative, mode="soft", wrap=True)
            return pack["text"]
        except ImportError:
            pass
    return text


def resolve_audit_script(root: Path, audit_name: str) -> Path:
    rel = ALLOWED_AUDIT_SCRIPTS.get(audit_name)
    if rel is None:
        raise SandboxError(f"Unknown audit: {audit_name}")
    path = _resolve_under_root(root, rel)
    if not path.is_file():
        raise FileNotFoundError(rel)
    return path