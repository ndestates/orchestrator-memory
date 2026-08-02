"""`orchestrator memory` — always-on memory host CLI (any project).

Delegates to bundled/dev ``scripts/memory_agent.py`` and
``scripts/session-memory-brief.py`` with a resolved project root.

Memory data defaults to ``<project>/reports/memory/memory.db`` (gitignored).
Optional operator-global store: ``ORCHESTRATOR_HOME`` / ``~/.orchestrator``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from ..template_root import template_root


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    # Ensure scripts/ is importable for _engine.*
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec.loader.exec_module(mod)
    return mod


def resolve_project_root(path: str | Path | None = None) -> Path:
    """Project whose memory DB we use (not the template root)."""
    if path is not None and str(path).strip():
        return Path(path).expanduser().resolve()
    env = (os.environ.get("ORCHESTRATOR_PROJECT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def resolve_memory_home() -> Path:
    """Optional global operator home (cross-project)."""
    env = (os.environ.get("ORCHESTRATOR_HOME") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.home().resolve() / ".orchestrator"


def memory_db_for(project: Path, *, scope: str = "project") -> Path:
    if scope == "global":
        return resolve_memory_home() / "memory" / "memory.db"
    return project / "reports" / "memory" / "memory.db"


def _engine_scripts() -> Path:
    root = template_root()
    scripts = root / "scripts"
    if not (scripts / "memory_agent.py").is_file():
        raise RuntimeError(
            f"memory_agent.py not found under template root {root} "
            "(install host package with bundled scripts or set ORCHESTRATOR_TEMPLATE_ROOT)"
        )
    return scripts


def run_memory_argv(
    argv: list[str],
    *,
    project: Path | None = None,
    scope: str = "project",
) -> int:
    """Run memory_agent.main with --root injected."""
    project = project or resolve_project_root()
    scripts = _engine_scripts()
    ma = _load_script("orch_memory_agent", scripts / "memory_agent.py")

    # When scope=global, point root at ORCHESTRATOR_HOME layout
    if scope == "global":
        home = resolve_memory_home()
        (home / "memory" / "inbox").mkdir(parents=True, exist_ok=True)
        # memory_agent uses root/reports/memory — emulate with home as root
        # by setting a synthetic layout: home/reports/memory
        reports = home / "reports" / "memory"
        reports.mkdir(parents=True, exist_ok=True)
        inbox = reports / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        root = home
    else:
        root = project
        (root / "reports" / "memory" / "inbox").mkdir(parents=True, exist_ok=True)

    # Inject --root after command if not already present
    args = list(argv)
    if "--root" not in args:
        # memory_agent: --root is top-level before subcommand
        # rebuild: [cmd, ...] -> [--root, path, cmd, ...]
        if args and not args[0].startswith("-"):
            args = ["--root", str(root), *args]
        else:
            args = ["--root", str(root), *args]
    return int(ma.main(args))


def run_brief(
    *,
    project: Path | None = None,
    seed: bool = False,
    as_json: bool = False,
    scope: str = "project",
) -> int:
    project = project or resolve_project_root()
    scripts = _engine_scripts()
    brief = _load_script("orch_session_memory_brief", scripts / "session-memory-brief.py")
    if scope == "global":
        root = resolve_memory_home()
        (root / "reports" / "memory" / "inbox").mkdir(parents=True, exist_ok=True)
    else:
        root = project
    argv: list[str] = ["--root", str(root)]
    if seed:
        argv.append("--seed")
    if as_json:
        argv.append("--json")
    return int(brief.main(argv))


def run(args: Any) -> int:
    """Dispatch from argparse Namespace (orchestrator memory …)."""
    path = getattr(args, "path", None)
    project = resolve_project_root(path if path else ".")
    scope = str(getattr(args, "scope", "project") or "project")
    sub = getattr(args, "memory_command", None) or getattr(args, "memory_cmd", None)

    if sub == "brief":
        return run_brief(
            project=project,
            seed=bool(getattr(args, "seed", False)),
            as_json=bool(getattr(args, "json", False)),
            scope=scope,
        )

    # Map CLI subcommands to memory_agent argv
    if sub == "status":
        return run_memory_argv(["status"], project=project, scope=scope)
    if sub == "models":
        return run_memory_argv(["models"], project=project, scope=scope)
    if sub == "agents":
        return run_memory_argv(["agents"], project=project, scope=scope)
    if sub == "list":
        lim = int(getattr(args, "limit", 20) or 20)
        return run_memory_argv(["list", "--limit", str(lim)], project=project, scope=scope)
    if sub == "seed":
        return run_memory_argv(["seed-situation"], project=project, scope=scope)
    if sub == "ingest":
        text = getattr(args, "text", None) or ""
        source = getattr(args, "source", None) or "cli"
        if getattr(args, "file", None):
            return run_memory_argv(
                ["ingest-file", str(Path(args.file).resolve())],
                project=project,
                scope=scope,
            )
        if not text:
            print("orchestrator memory ingest: require --text or --file", file=sys.stderr)
            return 2
        return run_memory_argv(
            ["ingest", "--text", text, "--source", source],
            project=project,
            scope=scope,
        )
    if sub == "query":
        q = getattr(args, "question", None) or ""
        if not q:
            print("orchestrator memory query: require a question", file=sys.stderr)
            return 2
        return run_memory_argv(["query", q], project=project, scope=scope)
    if sub == "consolidate":
        return run_memory_argv(["consolidate"], project=project, scope=scope)
    if sub == "watch":
        interval = int(getattr(args, "interval", 5) or 5)
        return run_memory_argv(
            ["watch", "--interval", str(interval)], project=project, scope=scope
        )
    if sub == "serve":
        port = int(getattr(args, "port", 8888) or 8888)
        every = int(getattr(args, "consolidate_every", 30) or 30)
        return run_memory_argv(
            [
                "serve",
                "--port",
                str(port),
                "--consolidate-every",
                str(every),
            ],
            project=project,
            scope=scope,
        )
    if sub == "db-path":
        print(memory_db_for(project, scope=scope))
        return 0

    print(f"orchestrator memory: unknown subcommand {sub!r}", file=sys.stderr)
    return 2
