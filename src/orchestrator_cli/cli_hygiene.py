"""Host CLI hygiene after init/upgrade.

Keeps ``pip`` package metadata aligned with the template ``VERSION`` so
``orchestrator version`` does not show stale e.g. 1.9.1 after a 1.9.2+ upgrade.

Runs automatically from the clean-deploy flow unless
``ORCHESTRATOR_SKIP_CLI_HYGIENE=1``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from .template_root import template_root
from .version import package_metadata_version, template_version


def hygiene_suppressed() -> bool:
    return os.environ.get("ORCHESTRATOR_SKIP_CLI_HYGIENE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "off",
    )


def _core(v: str) -> str:
    return (v or "").strip().lstrip("v").split("-")[0].split("+")[0]


def _pip_install(args: list[str], *, timeout: int = 300) -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pip", "install", *args]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return int(r.returncode), out[-800:] if out else ""
    except Exception as exc:
        return 1, str(exc)


def refresh_host_cli(*, version: str | None = None) -> dict[str, Any]:
    """Reinstall host CLI to match *version* (default: template VERSION).

    Strategy:
    1. If template root has ``pyproject.toml`` → ``pip install -e <root>`` (dev) or
       ``pip install <root>`` when not a git checkout (GitHub materialize cache).
    2. Else → ``pip install -U orchestrator==<version>``
    3. Confirm package metadata matches (core version for hatch core-only wheels).
    """
    result: dict[str, Any] = {
        "ran": False,
        "ok": False,
        "skipped": False,
        "method": None,
        "version_target": None,
        "metadata_before": package_metadata_version(),
        "metadata_after": None,
        "message": "",
        "detail": "",
    }
    if hygiene_suppressed():
        result["skipped"] = True
        result["message"] = "CLI hygiene skipped (ORCHESTRATOR_SKIP_CLI_HYGIENE=1)"
        return result

    try:
        target_ver = (version or template_version()).lstrip("v")
    except Exception as exc:
        result["message"] = f"CLI hygiene aborted: cannot resolve version ({exc})"
        return result
    result["version_target"] = target_ver
    result["ran"] = True

    root = template_root()
    pyproject = root / "pyproject.toml"
    code = 1
    detail = ""

    if pyproject.is_file():
        # Editable when source tree (has .git); plain install for materialize cache
        editable = (root / ".git").exists() or (root / ".git").is_file()
        if editable:
            result["method"] = "pip_editable_template_root"
            code, detail = _pip_install(["-e", str(root), "--quiet"])
        else:
            result["method"] = "pip_path_template_root"
            code, detail = _pip_install([str(root), "--quiet"])
        if code != 0:
            result["method"] = "pip_pypi_fallback"
            code, detail = _pip_install(
                ["-U", f"orchestrator=={_core(target_ver)}", "--quiet"]
            )
    else:
        result["method"] = "pip_pypi"
        code, detail = _pip_install(
            ["-U", f"orchestrator=={_core(target_ver)}", "--quiet"]
        )

    result["detail"] = detail
    after = package_metadata_version()
    result["metadata_after"] = after

    if code != 0:
        result["ok"] = False
        result["message"] = (
            f"CLI hygiene failed (exit {code}); pip metadata may stay "
            f"{result['metadata_before']!r}. Re-run: pip install -U "
            f"'orchestrator=={_core(target_ver)}'"
        )
        return result

    if after and (
        after == target_ver
        or _core(after) == _core(target_ver)
        or after == _core(target_ver)
    ):
        result["ok"] = True
        result["message"] = (
            f"CLI hygiene ok: pip metadata {result['metadata_before']!r} → {after!r} "
            f"(target {target_ver}, method={result['method']})"
        )
    else:
        result["ok"] = False
        result["message"] = (
            f"CLI hygiene ran but metadata still {after!r} "
            f"(wanted {target_ver}); try: pip install -U "
            f"'orchestrator=={_core(target_ver)}'"
        )
    return result
