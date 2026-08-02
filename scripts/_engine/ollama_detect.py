"""Detect local Ollama installation and API reachability (host, DDEV, docker-compose)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
MANIFEST_CANDIDATES = (
    ".grok/project-manifest.yaml",
    ".github/project-manifest.yaml",
    ".claude/project-manifest.yaml",
)
LOCAL_LLM_VALUES = frozenset({"none", "ollama"})
OLLAMA_RUNTIME_VALUES = frozenset({"auto", "host", "ddev", "docker-compose"})
ENV_MANAGER_VALUES = frozenset({"ddev", "docker-compose", "local"})
RUNTIME_BLOCK_RE = re.compile(r"runtime:\s*\n((?:[ \t]+[^\n]+\n)+)", re.MULTILINE)
LOCAL_LLM_RE = re.compile(r"^\s*local_llm:\s*\"?([^\"\n#]+)\"?", re.MULTILINE)
OLLAMA_RUNTIME_RE = re.compile(r"^\s*ollama_runtime:\s*\"?([^\"\n#]+)\"?", re.MULTILINE)
ENV_MANAGER_RE = re.compile(
    r"^\s*environment_manager:\s*\"?([^\"\n#]+)\"?", re.MULTILINE
)
COMPOSE_CANDIDATES = ("compose.yaml", "docker-compose.yml", "docker-compose.yaml")
DDEV_OLLAMA_MARKERS = (
    ".ddev/docker-compose.ollama.yaml",
    ".ddev/commands/web/ollama",
)
COMPOSE_OLLAMA_MARKERS = (
    "docker-compose.ollama.yaml",
    "compose.ollama.yaml",
)


def find_manifest_path(root: Path) -> Path | None:
    for rel in MANIFEST_CANDIDATES:
        path = root / rel
        if path.is_file():
            return path
    return None


def _runtime_block(manifest_text: str) -> str:
    match = RUNTIME_BLOCK_RE.search(manifest_text)
    return match.group(1) if match else ""


def _parse_runtime_field(manifest_text: str, pattern: re.Pattern[str], allowed: frozenset[str], default: str) -> str:
    block = _runtime_block(manifest_text)
    if not block:
        return default
    match = pattern.search(block)
    if not match:
        return default
    value = match.group(1).strip().strip('"').strip("'")
    return value if value in allowed else default


def parse_local_llm(manifest_text: str) -> str:
    return _parse_runtime_field(manifest_text, LOCAL_LLM_RE, LOCAL_LLM_VALUES, "none")


def parse_ollama_runtime(manifest_text: str) -> str:
    return _parse_runtime_field(
        manifest_text, OLLAMA_RUNTIME_RE, OLLAMA_RUNTIME_VALUES, "auto"
    )


def parse_environment_manager(manifest_text: str) -> str:
    return _parse_runtime_field(
        manifest_text, ENV_MANAGER_RE, ENV_MANAGER_VALUES, "local"
    )


def find_compose_file(root: Path) -> str:
    for name in COMPOSE_CANDIDATES:
        if (root / name).is_file():
            return name
    return ""


def runtime_signals(root: Path) -> dict[str, Any]:
    has_ddev = (root / ".ddev/config.yaml").is_file()
    compose_file = find_compose_file(root)
    has_compose = bool(compose_file)
    ddev_ollama_configured = any((root / rel).exists() for rel in DDEV_OLLAMA_MARKERS)
    compose_ollama_configured = any((root / rel).is_file() for rel in COMPOSE_OLLAMA_MARKERS)
    if not compose_ollama_configured and compose_file:
        text = (root / compose_file).read_text(encoding="utf-8", errors="replace")
        compose_ollama_configured = bool(re.search(r"^\s*ollama:\s*$", text, re.MULTILINE))
    return {
        "has_ddev": has_ddev,
        "has_compose": has_compose,
        "compose_file": compose_file,
        "ddev_ollama_configured": ddev_ollama_configured,
        "compose_ollama_configured": compose_ollama_configured,
    }


def resolve_ollama_target(
    *,
    requested: str,
    environment_manager: str,
    signals: dict[str, Any],
) -> str:
    if requested in {"host", "ddev", "docker-compose"}:
        return requested
    if environment_manager == "ddev" or signals["has_ddev"]:
        return "ddev"
    if environment_manager == "docker-compose" or signals["has_compose"]:
        return "docker-compose"
    return "host"


def resolve_ollama_host() -> str:
    host = os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).strip()
    if not host:
        host = DEFAULT_OLLAMA_HOST
    if "://" not in host:
        host = f"http://{host}"
    return host.rstrip("/")


def _run_cmd(argv: list[str], *, cwd: Path, timeout: float = 15.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def detect_binary() -> dict[str, Any]:
    path = shutil.which("ollama")
    version = ""
    if path:
        try:
            proc = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if proc.stdout or proc.stderr:
                version = (proc.stdout or proc.stderr).strip().splitlines()[0]
        except (OSError, subprocess.TimeoutExpired):
            version = ""
    return {
        "ollama_binary": "yes" if path else "no",
        "ollama_binary_path": path or "",
        "ollama_version": version,
    }


def detect_api(host: str | None = None, timeout: float = 3.0) -> dict[str, Any]:
    base = (host or resolve_ollama_host()).rstrip("/")
    url = f"{base}/api/tags"
    models_count = 0
    model_names: list[str] = []
    api_state = "unreachable"
    note = ""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                note = f"unexpected status {resp.status}"
            else:
                payload = json.loads(resp.read().decode("utf-8"))
                models = payload.get("models") or []
                if isinstance(models, list):
                    models_count = len(models)
                    for m in models:
                        if isinstance(m, dict):
                            name = str(m.get("name") or m.get("model") or "").strip()
                            if name:
                                model_names.append(name)
                api_state = "reachable"
    except urllib.error.URLError as exc:
        note = str(exc.reason) if getattr(exc, "reason", None) else str(exc)
    except (TimeoutError, json.JSONDecodeError, OSError) as exc:
        note = str(exc)
    return {
        "ollama_host": base,
        "ollama_api": api_state,
        "ollama_models_count": models_count,
        "ollama_model_names": model_names,
        "ollama_api_note": note,
    }


def _probe_via_curl(url: str, *, cwd: Path, timeout: float = 10.0) -> dict[str, Any]:
    proc = _run_cmd(["curl", "-sf", f"{url.rstrip('/')}/api/tags"], cwd=cwd, timeout=timeout)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "curl failed").strip()
        return {
            "ollama_host": url.rstrip("/"),
            "ollama_api": "unreachable",
            "ollama_models_count": 0,
            "ollama_api_note": err[:300],
        }
    try:
        payload = json.loads(proc.stdout)
        models = payload.get("models") or []
        count = len(models) if isinstance(models, list) else 0
    except json.JSONDecodeError:
        return {
            "ollama_host": url.rstrip("/"),
            "ollama_api": "unreachable",
            "ollama_models_count": 0,
            "ollama_api_note": "invalid json from curl",
        }
    return {
        "ollama_host": url.rstrip("/"),
        "ollama_api": "reachable",
        "ollama_models_count": count,
        "ollama_api_note": "",
    }


def detect_ddev_ollama(root: Path, *, configured: bool) -> dict[str, Any]:
    internal = "http://ollama:11434"
    external = DEFAULT_OLLAMA_HOST
    ddev_running = "no"
    service_running = "no"
    note = ""

    if not shutil.which("ddev"):
        note = "ddev not on PATH"
        return {
            "ollama_runtime": "ddev",
            "ollama_service_configured": "yes" if configured else "no",
            "ddev_running": ddev_running,
            "ollama_service_running": service_running,
            "ollama_host_internal": internal,
            "ollama_host_external": external,
            "ollama_api": "unreachable",
            "ollama_models_count": 0,
            "ollama_api_note": note,
            "ollama_probe_via": "ddev",
        }

    describe = _run_cmd(["ddev", "describe", "-j"], cwd=root, timeout=20)
    if describe.returncode == 0 and describe.stdout.strip():
        ddev_running = "yes"
        try:
            payload = json.loads(describe.stdout)
            raw = describe.stdout
            if "11434" in raw:
                external = DEFAULT_OLLAMA_HOST
        except json.JSONDecodeError:
            pass
    else:
        note = "DDEV not running — ddev start"
        return {
            "ollama_runtime": "ddev",
            "ollama_service_configured": "yes" if configured else "no",
            "ddev_running": ddev_running,
            "ollama_service_running": service_running,
            "ollama_host_internal": internal,
            "ollama_host_external": external,
            "ollama_api": "unreachable",
            "ollama_models_count": 0,
            "ollama_api_note": note,
            "ollama_probe_via": "ddev",
        }

    if configured:
        for argv in (
            ["ddev", "exec", "curl", "-sf", "http://ollama:11434/api/tags"],
            ["ddev", "exec", "-s", "ollama", "curl", "-sf", "http://127.0.0.1:11434/api/tags"],
        ):
            proc = _run_cmd(argv, cwd=root, timeout=20)
            if proc.returncode == 0 and proc.stdout.strip():
                service_running = "yes"
                try:
                    payload = json.loads(proc.stdout)
                    models = payload.get("models") or []
                    count = len(models) if isinstance(models, list) else 0
                except json.JSONDecodeError:
                    count = 0
                host_api = detect_api(external)
                if host_api["ollama_api"] != "reachable":
                    host_api = {
                        "ollama_host": internal,
                        "ollama_api": "reachable",
                        "ollama_models_count": count,
                        "ollama_api_note": (
                            "reachable inside DDEV (ollama:11434); "
                            f"set OLLAMA_HOST={external} for host agents"
                        ),
                    }
                return {
                    "ollama_runtime": "ddev",
                    "ollama_service_configured": "yes",
                    "ddev_running": ddev_running,
                    "ollama_service_running": service_running,
                    "ollama_host_internal": internal,
                    "ollama_host_external": external,
                    "ollama_probe_via": "ddev",
                    **host_api,
                }

    host_api = detect_api(external)
    return {
        "ollama_runtime": "ddev",
        "ollama_service_configured": "yes" if configured else "no",
        "ddev_running": ddev_running,
        "ollama_service_running": service_running,
        "ollama_host_internal": internal,
        "ollama_host_external": external,
        "ollama_probe_via": "ddev",
        **host_api,
    }


def detect_compose_ollama(root: Path, *, configured: bool, compose_file: str) -> dict[str, Any]:
    internal = "http://ollama:11434"
    external = DEFAULT_OLLAMA_HOST
    compose_running = "no"
    service_running = "no"
    note = ""

    if not shutil.which("docker"):
        note = "docker not on PATH"
        return {
            "ollama_runtime": "docker-compose",
            "ollama_service_configured": "yes" if configured else "no",
            "compose_file": compose_file,
            "compose_running": compose_running,
            "ollama_service_running": service_running,
            "ollama_host_internal": internal,
            "ollama_host_external": external,
            "ollama_api": "unreachable",
            "ollama_models_count": 0,
            "ollama_api_note": note,
            "ollama_probe_via": "docker-compose",
        }

    compose_argv = ["docker", "compose"]
    if compose_file:
        compose_argv.extend(["-f", compose_file])
    ollama_overlay = root / "docker-compose.ollama.yaml"
    if ollama_overlay.is_file() and compose_file:
        compose_argv.extend(["-f", "docker-compose.ollama.yaml"])

    ps = _run_cmd([*compose_argv, "ps", "-q", "ollama"], cwd=root, timeout=20)
    if ps.returncode == 0 and ps.stdout.strip():
        compose_running = "yes"
        service_running = "yes"

    if service_running == "yes":
        exec_probe = _run_cmd(
            [*compose_argv, "exec", "-T", "ollama", "curl", "-sf", "http://127.0.0.1:11434/api/tags"],
            cwd=root,
            timeout=20,
        )
        if exec_probe.returncode == 0 and exec_probe.stdout.strip():
            try:
                payload = json.loads(exec_probe.stdout)
                models = payload.get("models") or []
                count = len(models) if isinstance(models, list) else 0
            except json.JSONDecodeError:
                count = 0
            host_api = detect_api(external)
            if host_api["ollama_api"] != "reachable":
                host_api = {
                    "ollama_host": internal,
                    "ollama_api": "reachable",
                    "ollama_models_count": count,
                    "ollama_api_note": (
                        "reachable in compose network (ollama:11434); "
                        f"host agents use OLLAMA_HOST={external}"
                    ),
                }
            return {
                "ollama_runtime": "docker-compose",
                "ollama_service_configured": "yes" if configured else "no",
                "compose_file": compose_file,
                "compose_running": compose_running,
                "ollama_service_running": service_running,
                "ollama_host_internal": internal,
                "ollama_host_external": external,
                "ollama_probe_via": "docker-compose",
                **host_api,
            }

    host_api = detect_api(external)
    if host_api["ollama_api"] != "reachable" and not configured:
        note = "no ollama service in compose — bash scripts/install-ollama-compose.sh"
        host_api["ollama_api_note"] = note
    elif host_api["ollama_api"] != "reachable" and configured:
        note = "ollama service configured but not running — docker compose up -d ollama"
        host_api["ollama_api_note"] = note
    return {
        "ollama_runtime": "docker-compose",
        "ollama_service_configured": "yes" if configured else "no",
        "compose_file": compose_file,
        "compose_running": compose_running,
        "ollama_service_running": service_running,
        "ollama_host_internal": internal,
        "ollama_host_external": external,
        "ollama_probe_via": "docker-compose",
        **host_api,
    }


def install_hint(target: str, *, configured: bool) -> str:
    if target == "ddev":
        return (
            "bash scripts/install-ollama-ddev.sh"
            if not configured
            else "ddev start && ddev restart"
        )
    if target == "docker-compose":
        return (
            "bash scripts/install-ollama-compose.sh"
            if not configured
            else "docker compose -f docker-compose.ollama.yaml up -d ollama"
        )
    return "bash scripts/install-ollama.sh"


def evaluate(root: Path | None = None) -> dict[str, Any]:
    project_root = (root or Path.cwd()).resolve()
    manifest_file = find_manifest_path(project_root)
    manifest_text = ""
    if manifest_file:
        manifest_text = manifest_file.read_text(encoding="utf-8", errors="replace")

    manifest_local_llm = parse_local_llm(manifest_text) if manifest_text else "none"
    manifest_ollama_runtime = parse_ollama_runtime(manifest_text) if manifest_text else "auto"
    environment_manager = parse_environment_manager(manifest_text) if manifest_text else "local"
    signals = runtime_signals(project_root)
    target = resolve_ollama_target(
        requested=manifest_ollama_runtime,
        environment_manager=environment_manager,
        signals=signals,
    )

    binary = detect_binary()
    if target == "ddev":
        runtime_report = detect_ddev_ollama(
            project_root, configured=signals["ddev_ollama_configured"]
        )
    elif target == "docker-compose":
        runtime_report = detect_compose_ollama(
            project_root,
            configured=signals["compose_ollama_configured"],
            compose_file=signals["compose_file"],
        )
    else:
        runtime_report = detect_api()
        runtime_report.update(
            {
                "ollama_runtime": "host",
                "ollama_service_configured": "n/a",
                "ollama_host_internal": resolve_ollama_host(),
                "ollama_host_external": resolve_ollama_host(),
                "ollama_probe_via": "host",
            }
        )

    local_llm_ready = "n/a"
    ollama_note = ""
    if manifest_local_llm == "ollama":
        if runtime_report["ollama_api"] == "reachable":
            local_llm_ready = "yes"
        else:
            local_llm_ready = "no"
            service_configured = runtime_report.get("ollama_service_configured")
            if service_configured == "no":
                ollama_note = (
                    "manifest local_llm=ollama but Ollama service not configured — "
                    + install_hint(target, configured=False)
                )
            elif target == "host" and binary["ollama_binary"] == "no":
                ollama_note = (
                    "manifest local_llm=ollama but ollama CLI missing — "
                    + install_hint("host", configured=True)
                )
            else:
                hint = install_hint(
                    target,
                    configured=service_configured == "yes",
                )
                api_note = runtime_report.get("ollama_api_note", "")
                ollama_note = api_note or f"manifest local_llm=ollama but API unreachable — {hint}"
    elif target == "host" and binary["ollama_binary"] == "yes" and runtime_report["ollama_api"] != "reachable":
        ollama_note = "ollama CLI present but API unreachable — start Ollama service"

    return {
        "project_root": str(project_root),
        "manifest_file": str(manifest_file.relative_to(project_root)) if manifest_file else "",
        "manifest_local_llm": manifest_local_llm,
        "manifest_ollama_runtime": manifest_ollama_runtime,
        "environment_manager": environment_manager,
        "ollama_runtime": target,
        "has_ddev": "yes" if signals["has_ddev"] else "no",
        "has_compose": "yes" if signals["has_compose"] else "no",
        "compose_file": signals["compose_file"],
        **binary,
        **runtime_report,
        "local_llm_ready": local_llm_ready,
        "ollama_note": ollama_note,
    }


def format_text(report: dict[str, Any]) -> str:
    lines = [f"{key}={value}" for key, value in report.items()]
    return "\n".join(lines) + "\n"