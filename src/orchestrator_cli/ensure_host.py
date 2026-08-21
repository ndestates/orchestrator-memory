"""Host ensure wrappers — MCP venv + host tools (rg).

Thin CLI over existing scripts:

- ``scripts/ensure-mcp-host.sh``
- ``scripts/install-host-tools.sh``

Resolves scripts from ``--path`` (app/repo cwd) first, else template root.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .template_root import template_root


def resolve_project_root(path: Path | None = None) -> Path:
    """Prefer *path*/cwd when it has scripts/; else template_root()."""
    candidates: list[Path] = []
    if path is not None:
        candidates.append(path.resolve())
    candidates.append(Path.cwd().resolve())
    try:
        candidates.append(template_root().resolve())
    except Exception:
        pass
    for root in candidates:
        if (root / "scripts" / "ensure-mcp-host.sh").is_file() or (
            root / "scripts" / "install-host-tools.sh"
        ).is_file():
            return root
    if path is not None:
        return path.resolve()
    return Path.cwd().resolve()


def _run_script(
    script: Path, args: list[str], *, timeout: int = 600
) -> dict[str, Any]:
    if not script.is_file():
        return {
            "ok": False,
            "exit_code": 2,
            "script": str(script),
            "args": args,
            "stdout": "",
            "stderr": f"missing script: {script}",
            "skipped": True,
        }
    cmd = ["bash", str(script), *args]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=str(script.parent.parent),
        )
        return {
            "ok": r.returncode == 0,
            "exit_code": int(r.returncode),
            "script": str(script),
            "args": args,
            "stdout": (r.stdout or "")[-2000:],
            "stderr": (r.stderr or "")[-2000:],
            "skipped": False,
            "command": cmd,
        }
    except Exception as exc:
        return {
            "ok": False,
            "exit_code": 1,
            "script": str(script),
            "args": args,
            "stdout": "",
            "stderr": str(exc),
            "skipped": False,
            "command": cmd,
        }


def run_ensure(
    *,
    path: Path | None = None,
    mcp: bool = False,
    host_tools: bool = True,
    check: bool = False,
    force: bool = False,
    yes: bool = False,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run selected ensure steps. Default: host_tools only (MCP opt-in via --mcp)."""
    root = resolve_project_root(path)
    steps: dict[str, Any] = {}
    report: dict[str, Any] = {
        "action": "ensure",
        "root": str(root),
        "check": check,
        "mcp": mcp,
        "host_tools": host_tools,
        "steps": steps,
        "ok": True,
        "message": "",
    }

    if not mcp and not host_tools:
        report["ok"] = False
        report["message"] = "nothing selected — pass --mcp and/or --host-tools"
        return report

    if mcp:
        script = root / "scripts" / "ensure-mcp-host.sh"
        args: list[str] = []
        if check:
            args.append("--check")
        elif force:
            args.append("--force")
        if quiet:
            args.append("--quiet")
        steps["mcp"] = _run_script(script, args)
        if steps["mcp"].get("skipped") and not script.is_file():
            steps["mcp"]["message"] = "ensure-mcp-host.sh not present in this tree"

    if host_tools:
        script = root / "scripts" / "install-host-tools.sh"
        args = []
        if check:
            args.append("--check")
        elif yes:
            args.append("--yes")
        # default script mode: check + install if possible (interactive may fail headless)
        if quiet and "--check" not in args and not yes:
            # non-interactive prefer check unless repair requested
            args.append("--check")
        steps["host_tools"] = _run_script(script, args)
        if steps["host_tools"].get("skipped") and not script.is_file():
            steps["host_tools"]["message"] = (
                "install-host-tools.sh not present in this tree"
            )

    failed = [
        name
        for name, st in steps.items()
        if not st.get("ok") and not st.get("skipped")
    ]
    missing = [name for name, st in steps.items() if st.get("skipped")]
    report["ok"] = not failed
    if report["ok"] and not missing:
        mode = "check" if check else "ensure"
        report["message"] = f"ensure {mode} ok at {root} ({', '.join(steps)})"
    elif report["ok"] and missing:
        report["message"] = (
            f"ensure partial at {root}: ok={[n for n in steps if n not in missing]}; "
            f"missing_scripts={missing}"
        )
        # missing scripts is not a hard fail if at least one step ran ok
        if not any(st.get("ok") for st in steps.values()):
            report["ok"] = False
    else:
        report["message"] = f"ensure failed steps={failed} at {root}"
    return report


def format_human(report: dict[str, Any]) -> str:
    lines = [report.get("message") or "ensure", f"  root={report.get('root')}"]
    for name, st in (report.get("steps") or {}).items():
        status = (
            "SKIP"
            if st.get("skipped")
            else ("OK" if st.get("ok") else f"FAIL({st.get('exit_code')})")
        )
        lines.append(f"  {name}: {status}")
        # short last non-empty output line
        for stream in ("stdout", "stderr"):
            text = (st.get(stream) or "").strip()
            if text:
                last = text.splitlines()[-1]
                lines.append(f"    {last[:160]}")
                break
    return "\n".join(lines)


def to_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, default=str)
