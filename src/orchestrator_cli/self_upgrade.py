"""Host CLI self-upgrade (package on PATH, not app template deploy).

Upgrades the *orchestrator* host tool so ``orchestrator version`` matches a
target release. App trees use ``orchestrator upgrade <path>`` instead.

Channels (auto-detect, override with ``--method``):

1. **uv tool** — ``~/.local/share/uv/tools/orchestrator`` (preferred when present)
2. **pip** — via :func:`cli_hygiene.refresh_host_cli` (editable template or PyPI)

Safety: default is **plan only**. Pass ``--yes`` to apply (``--dry-run`` forces plan).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import cli_hygiene
from .remote_version import best_available, fetch_latest_release_version
from .template_root import dev_repo_root, template_root
from .version import cli_version, is_newer, package_metadata_version, template_version


def _normalize(v: str | None) -> str:
    return (v or "").strip().lstrip("v")


def _core(v: str) -> str:
    return _normalize(v).split("-")[0].split("+")[0]


def detect_channel() -> str:
    """Return ``uv_tool`` | ``pip`` | ``unknown`` for the running CLI."""
    exe = Path(sys.executable).resolve()
    parts = {p.lower() for p in exe.parts}
    # Typical: ~/.local/share/uv/tools/orchestrator/bin/python
    if "uv" in parts and "tools" in parts:
        return "uv_tool"
    # Shebang of argv[0] may still point at uv when run via wrapper
    try:
        prog = Path(sys.argv[0]).resolve()
        if prog.is_file():
            head = prog.read_text(encoding="utf-8", errors="replace")[:200]
            if "uv/tools/orchestrator" in head or "/uv/tools/" in head:
                return "uv_tool"
    except OSError:
        pass
    if package_metadata_version() is not None:
        return "pip"
    if shutil.which("uv"):
        # uv present but not clearly a uv-tool install — still prefer uv path when forced
        return "pip"
    return "unknown"


def find_uv() -> str | None:
    for candidate in (
        shutil.which("uv"),
        str(Path.home() / ".local" / "bin" / "uv"),
        str(Path.home() / ".cargo" / "bin" / "uv"),
    ):
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def resolve_target_version(
    *,
    to_version: str | None = None,
    from_github: str | bool | None = None,
) -> tuple[str, str]:
    """Return ``(version, source)`` for the host CLI target."""
    if to_version:
        return _normalize(to_version), "flag:to"

    if from_github is not None:
        if isinstance(from_github, str) and from_github not in ("", "latest", "true"):
            return _normalize(from_github), "flag:from-github"
        remote = fetch_latest_release_version()
        if remote and remote.version:
            return _normalize(remote.version), remote.source or "github"
        # fall through to local best

    try:
        local = template_version()
    except Exception:
        local = None
    remote = fetch_latest_release_version()
    ver, source = best_available(local, remote)
    if ver:
        return _normalize(ver), source
    if local:
        return _normalize(local), "local_template"
    cur = cli_version()
    return _normalize(cur), "cli_current"


def _template_root_for_install() -> Path | None:
    """Best local tree to install the host package from."""
    env = (os.environ.get("ORCHESTRATOR_TEMPLATE_ROOT") or "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "pyproject.toml").is_file():
            return p
    root = dev_repo_root()
    if root and (root / "pyproject.toml").is_file():
        return root
    try:
        tr = template_root()
        if (tr / "pyproject.toml").is_file():
            return tr
    except Exception:
        pass
    return None


def _run(
    cmd: list[str], *, timeout: int = 600
) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return int(r.returncode), out[-1200:] if out else ""
    except Exception as exc:
        return 1, str(exc)


def plan_self_upgrade(
    *,
    to_version: str | None = None,
    from_github: str | bool | None = None,
    method: str = "auto",
) -> dict[str, Any]:
    """Build a self-upgrade plan without mutating the host install."""
    current = _normalize(cli_version())
    meta = package_metadata_version()
    target, source = resolve_target_version(
        to_version=to_version, from_github=from_github
    )
    channel = detect_channel() if method in ("", "auto", None) else method
    if channel not in ("uv_tool", "pip", "auto", "unknown"):
        channel = "auto"
    if channel == "auto":
        channel = detect_channel()
    if channel == "unknown":
        channel = "uv_tool" if find_uv() else "pip"

    root = _template_root_for_install()
    uv = find_uv()
    needs = is_newer(target, current) or (
        meta is not None and _core(meta) != _core(target) and current != target
    )
    # Always allow explicit reinstall when --to matches current (refresh)
    force_same = bool(to_version) and _normalize(to_version) == current

    plan: dict[str, Any] = {
        "action": "self-upgrade",
        "current": current,
        "package_metadata": meta,
        "target": target,
        "target_source": source,
        "channel": channel,
        "method": None,
        "needs_upgrade": needs or force_same,
        "already_current": (not needs) and not force_same,
        "template_root": str(root) if root else None,
        "uv": uv,
        "commands": [],
        "message": "",
        "ok": True,
    }

    if plan["already_current"]:
        plan["message"] = (
            f"host CLI already at {current} (target {target} via {source}) — nothing to do"
        )
        return plan

    if channel == "uv_tool":
        if not uv:
            plan["ok"] = False
            plan["message"] = (
                "channel=uv_tool but `uv` not found on PATH; "
                "install uv or use --method pip"
            )
            return plan
        if root is not None:
            plan["method"] = "uv_tool_from_path"
            plan["commands"] = [
                [uv, "tool", "install", "--force", "--from", str(root), "orchestrator"]
            ]
        else:
            plan["method"] = "uv_tool_pypi"
            plan["commands"] = [
                [uv, "tool", "install", "--force", f"orchestrator=={_core(target)}"]
            ]
        plan["message"] = (
            f"plan: uv-tool install host CLI {current} → {target} "
            f"(method={plan['method']}, source={source})"
        )
        return plan

    # pip path (hygiene)
    plan["method"] = "pip_hygiene"
    if root is not None:
        editable = (root / ".git").exists() or (root / ".git").is_file()
        if editable:
            plan["commands"] = [
                [sys.executable, "-m", "pip", "install", "-e", str(root)]
            ]
        else:
            plan["commands"] = [
                [sys.executable, "-m", "pip", "install", str(root)]
            ]
    else:
        plan["commands"] = [
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-U",
                f"orchestrator=={_core(target)}",
            ]
        ]
    plan["message"] = (
        f"plan: pip install host CLI {current} → {target} "
        f"(method={plan['method']}, source={source})"
    )
    return plan


def apply_self_upgrade(plan: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Execute a plan (or build then execute). Mutates host install."""
    plan = plan or plan_self_upgrade(**kwargs)
    result = dict(plan)
    result["applied"] = False
    result["dry_run"] = False

    if not plan.get("ok"):
        result["ok"] = False
        return result

    if plan.get("already_current"):
        result["ok"] = True
        result["applied"] = False
        return result

    channel = plan.get("channel")
    if channel == "uv_tool":
        cmds = plan.get("commands") or []
        if not cmds:
            result["ok"] = False
            result["message"] = "no uv commands in plan"
            return result
        code, detail = _run(cmds[0])
        result["detail"] = detail
        result["applied"] = code == 0
        result["ok"] = code == 0
        if code == 0:
            after = package_metadata_version() or cli_version()
            result["metadata_after"] = after
            result["message"] = (
                f"self-upgrade ok: host CLI → target {plan.get('target')} "
                f"(method={plan.get('method')}, metadata={after!r})"
            )
        else:
            result["message"] = (
                f"self-upgrade failed (exit {code}) via {plan.get('method')}. "
                f"Detail: {detail[-400:]}"
            )
        return result

    # pip via hygiene (reuses template root resolution when env set)
    hy = cli_hygiene.refresh_host_cli(version=str(plan.get("target") or ""))
    result["hygiene"] = hy
    result["applied"] = bool(hy.get("ran") and not hy.get("skipped"))
    result["ok"] = bool(hy.get("ok") or hy.get("skipped"))
    result["message"] = hy.get("message") or result.get("message")
    result["metadata_after"] = hy.get("metadata_after")
    result["method"] = hy.get("method") or plan.get("method")
    return result


def run_self_upgrade(
    *,
    to_version: str | None = None,
    from_github: str | bool | None = None,
    method: str = "auto",
    yes: bool = False,
    dry_run: bool = False,
    as_json: bool = False,
) -> tuple[int, dict[str, Any]]:
    """CLI entry: plan always; apply only when yes and not dry_run."""
    plan = plan_self_upgrade(
        to_version=to_version, from_github=from_github, method=method
    )
    do_apply = bool(yes) and not dry_run
    if not do_apply:
        plan["dry_run"] = True
        plan["applied"] = False
        if plan.get("ok") and not plan.get("already_current"):
            plan["message"] = (
                (plan.get("message") or "plan ready")
                + " — pass --yes to apply (default is dry-run)"
            )
        return (0 if plan.get("ok") else 1), plan

    result = apply_self_upgrade(plan)
    result["dry_run"] = False
    return (0 if result.get("ok") else 1), result


def format_human(result: dict[str, Any]) -> str:
    lines = [
        result.get("message") or "self-upgrade",
        f"  current={result.get('current')}  target={result.get('target')}  "
        f"channel={result.get('channel')}  method={result.get('method')}",
    ]
    if result.get("dry_run") and result.get("commands"):
        for cmd in result["commands"]:
            lines.append("  → " + " ".join(str(c) for c in cmd))
    if result.get("template_root"):
        lines.append(f"  template_root={result['template_root']}")
    return "\n".join(lines)


def to_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, default=str)
