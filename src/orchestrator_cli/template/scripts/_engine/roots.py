"""Resolve the orchestrator template root (wheel bundle, dev checkout, or explicit)."""

from __future__ import annotations

from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _ENGINE_DIR.parent
_DEV_FALLBACK = _SCRIPTS_DIR.parent

_TEMPLATE_ROOT: Path | None = None


def default_main_root(script_file: Path) -> Path:
    """Default root when a ``scripts/<name>.py`` shim is run as ``__main__``."""
    return script_file.resolve().parent.parent


def set_template_root(root: Path) -> None:
    """Pin the template root for subsequent engine calls (tests, CLI, shims)."""
    global _TEMPLATE_ROOT
    _TEMPLATE_ROOT = root.resolve()


def reset_template_root() -> None:
    """Clear an explicit pin (tests only)."""
    global _TEMPLATE_ROOT
    _TEMPLATE_ROOT = None


class _LazyRoot:
    """Path-like proxy so legacy ``ROOT / \"subdir\"`` keeps working."""

    def __truediv__(self, other: str | Path) -> Path:
        return get_template_root() / other

    def resolve(self) -> Path:
        return get_template_root().resolve()

    def __str__(self) -> str:
        return str(get_template_root())

    def __fspath__(self) -> str:
        return str(get_template_root())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Path):
            return get_template_root().resolve() == other.resolve()
        return NotImplemented

    def __hash__(self) -> int:
        raise TypeError("unhashable LazyRoot")


def lazy_root() -> _LazyRoot:
    """Legacy ``ROOT`` stand-in for scripts that build many path constants at import."""
    return _LazyRoot()


def get_template_root() -> Path:
    """Return the active template root.

    Priority: explicit ``set_template_root`` → installed ``orchestrator_cli`` →
    dev checkout (repo root above ``scripts/_engine/``).
    """
    if _TEMPLATE_ROOT is not None:
        return _TEMPLATE_ROOT
    try:
        from orchestrator_cli.template_root import template_root

        return template_root()
    except (ImportError, RuntimeError):
        return _DEV_FALLBACK