"""orchestrator CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .commands import check as check_cmd
from .commands import ensure as ensure_cmd
from .commands import install_persist as install_persist_cmd
from .commands import license as license_cmd
from .commands import memory as memory_cmd
from .commands import self_upgrade as self_upgrade_cmd
from .commands import status as status_cmd
from .commands import uninstall as uninstall_cmd
from .commands import version as version_cmd
from .flow import run_init, run_upgrade
from . import license_server as license_server_mod
from . import update_check


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="orchestrator", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    vp = sub.add_parser(
        "version",
        help="print host / template / app version matrix (SSOT=VERSION)",
    )
    vp.add_argument(
        "path",
        nargs="?",
        default=".",
        help="app or tree to report app lock for (default: cwd)",
    )
    vp.add_argument("--json", action="store_true", help="machine-readable matrix")

    lp = sub.add_parser("license", help="check license gate status (Phase 3.5)")
    lp.add_argument("--key", default=None, help="override ORCHESTRATOR_LICENSE_KEY for this check")

    lsp = sub.add_parser(
        "license-server",
        help="run reference POST /api/licenses/validate server (local/self-host)",
    )
    lsp.add_argument("--host", default=None, help="bind host (default 127.0.0.1)")
    lsp.add_argument("--port", type=int, default=None, help="bind port (default 8787)")

    sp = sub.add_parser("status", help="installed vs available version + drift")
    sp.add_argument("path", nargs="?", default=".", help="target project (default: cwd)")
    sp.add_argument("--json", action="store_true", help="machine-readable output")

    cp = sub.add_parser(
        "check",
        help="announce if install or upgrade is needed for a project (exit 2=upgrade, 3=not installed)",
    )
    cp.add_argument("path", nargs="?", default=".", help="target project (default: cwd)")
    cp.add_argument("--json", action="store_true", help="machine-readable output")
    cp.add_argument(
        "--quiet-ok",
        action="store_true",
        help="print nothing when up to date (still exit 0)",
    )

    for name, help_text in (
        ("init", "install the template into this project (clean-deploy flow)"),
        ("upgrade", "upgrade the template to a release (clean-deploy flow)"),
    ):
        ip = sub.add_parser(name, help=help_text)
        ip.add_argument("path", nargs="?", default=".")
        ip.add_argument("--to", "--version", dest="to", default=None)
        ip.add_argument("--profile", default=None)
        ip.add_argument("--selections", default=None, help="comma list or 'all' (default from bundle)")
        ip.add_argument("--no-pr", action="store_true")
        ip.add_argument("--dry-run", action="store_true")
        ip.add_argument(
            "--verify-bundle",
            action="store_true",
            help="after deploy, verify high-risk file hashes against template stamp (Phase 2)",
        )
        ip.add_argument(
            "--from-github",
            nargs="?",
            const="latest",
            default=None,
            metavar="TAG",
            help=(
                "fetch template from GitHub Releases (default: latest). "
                "Example: --from-github v1.8.5. Private: set GITHUB_TOKEN."
            ),
        )
        ip.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help=(
                "suppress per-file NEW/UPDATE/CONFLICT lines; print one-line summary only "
                "(agent-safe; cuts tool-output token cost)"
            ),
        )
        ip.add_argument(
            "--stash",
            action="store_true",
            help=(
                "if working tree is dirty: git stash push -u, deploy, then stash pop "
                "(keeps app WIP; needed for upgrades mid-feature work)"
            ),
        )
        if name == "upgrade":
            ip.add_argument(
                "--if-available",
                action="store_true",
                help="only upgrade when check reports a newer version; exit 0 if current",
            )
            ip.add_argument(
                "--yes",
                "-y",
                action="store_true",
                help="apply for real with --if-available / --from-github (without --yes: dry-run)",
            )

    su = sub.add_parser(
        "self-upgrade",
        help="upgrade the host CLI package on PATH (uv tool preferred; not app template deploy)",
    )
    su.add_argument(
        "--to",
        "--version",
        dest="to",
        default=None,
        help="target version (default: best of local template VERSION + GitHub latest)",
    )
    su.add_argument(
        "--from-github",
        nargs="?",
        const="latest",
        default=None,
        metavar="TAG",
        help="prefer GitHub Releases latest (or TAG) as the target version",
    )
    su.add_argument(
        "--method",
        choices=("auto", "uv_tool", "pip"),
        default="auto",
        help="install channel (default: auto-detect; uv tool when present)",
    )
    su.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="apply for real (without --yes: dry-run plan only)",
    )
    su.add_argument(
        "--dry-run",
        action="store_true",
        help="force plan-only even if --yes is set",
    )
    su.add_argument("--json", action="store_true", help="machine-readable output")

    ipp = sub.add_parser(
        "install-persist",
        help=(
            "optional: baseline ref + tools for THIS app repo only "
            "(never fleet/wave; multi-branch broadcast is OFF unless env opt-in)"
        ),
    )
    ipp.add_argument(
        "path",
        nargs="?",
        default=".",
        help="app repo that already has .orchestrator-version on the current branch",
    )
    ipp.add_argument(
        "--dry-run",
        action="store_true",
        help="describe actions only (no git writes)",
    )
    ipp.add_argument("--json", action="store_true", help="machine-readable output")

    en = sub.add_parser(
        "ensure",
        help="ensure host MCP venv and/or host tools (rg) via project scripts",
    )
    en.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project root with scripts/ (default: cwd; falls back to template root)",
    )
    en.add_argument(
        "--mcp",
        action="store_true",
        help="only ensure-mcp-host (default: both mcp and host-tools)",
    )
    en.add_argument(
        "--host-tools",
        action="store_true",
        help="only install-host-tools (default: both mcp and host-tools)",
    )
    en.add_argument(
        "--check",
        action="store_true",
        help="status only (no repair/install)",
    )
    en.add_argument(
        "--force",
        action="store_true",
        help="with MCP: rebuild venv even if healthy",
    )
    en.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="with host-tools: non-interactive install",
    )
    en.add_argument("--quiet", "-q", action="store_true", help="less script chatter")
    en.add_argument("--json", action="store_true", help="machine-readable output")

    up = sub.add_parser(
        "uninstall",
        help="remove orchestrator from a project and/or uninstall host npm/pip CLI packages",
    )
    up.add_argument("path", nargs="?", default=".", help="project root (default: cwd)")
    up.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="preview only (default)",
    )
    up.add_argument(
        "--apply",
        action="store_true",
        help="actually uninstall (disables dry-run)",
    )
    up.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="required with --apply to delete project files",
    )
    up.add_argument(
        "--host",
        action="store_true",
        help="uninstall global npm (@ndestates/orchestrator) and pip (orchestrator) packages",
    )
    up.add_argument(
        "--no-project",
        action="store_true",
        help="skip project path removal (host-only with --host)",
    )
    up.add_argument("--selections", default=None, help="bundle selections to reverse (default: default_selections)")
    up.add_argument("--remove-cache", action="store_true", help="also remove docs/codebase cache spine")
    up.add_argument("--remove-todo", action="store_true", help="also remove TODO/")
    up.add_argument("--remove-state", action="store_true", help="also remove STATE.md / VISION.md / loop-run-log.md")
    up.add_argument("--remove-memories", action="store_true", help="also remove .grok/memories (incl. who-i-am)")
    up.add_argument("--remove-manifests", action="store_true", help="also remove per-platform project-manifest.yaml")
    up.add_argument(
        "--force-template-source",
        action="store_true",
        help="allow running against the orchestrator template source repo (dangerous)",
    )
    up.add_argument("--json", action="store_true", help="machine-readable output")
    up.add_argument("--no-npm", action="store_true", help="with --host: skip npm uninstall")
    up.add_argument("--no-pip", action="store_true", help="with --host: skip pip uninstall")

    # Always-on memory (host CLI — any project; freeware OSS)
    mp = sub.add_parser(
        "memory",
        help="always-on project memory (ingest/query/consolidate/serve/brief)",
    )
    mp.add_argument(
        "--path",
        "--cwd",
        dest="path",
        default=".",
        help="project root for memory.db (default: cwd)",
    )
    mp.add_argument(
        "--scope",
        choices=("project", "global"),
        default="project",
        help="project DB under <path>/reports/memory or ~/.orchestrator (global)",
    )
    msub = mp.add_subparsers(dest="memory_command", required=True)

    def _mem_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--path",
            "--cwd",
            dest="path",
            default=None,
            help="project root (overrides parent --path; default: cwd)",
        )

    for _name, _help in (
        ("status", "memory + model/agent inventory"),
        ("models", "full model-route catalog picks"),
        ("agents", "full agent roster role picks"),
        ("seed", "seed VERSION/git/TODO/resume into memory"),
        ("consolidate", "consolidate unconsolidated memories"),
        ("db-path", "print resolved memory.db path"),
    ):
        _sp = msub.add_parser(_name, help=_help)
        _mem_common(_sp)
    mlb = msub.add_parser("list", help="list recent memories")
    _mem_common(mlb)
    mlb.add_argument("--limit", type=int, default=20)
    mi = msub.add_parser("ingest", help="ingest text or file")
    _mem_common(mi)
    mi.add_argument("--text", default=None)
    mi.add_argument("--file", default=None)
    mi.add_argument("--source", default="cli")
    mq = msub.add_parser("query", help="query memory")
    _mem_common(mq)
    mq.add_argument("question", help="natural language question")
    mb = msub.add_parser("brief", help="session-start lean memory brief")
    _mem_common(mb)
    mb.add_argument("--seed", action="store_true", help="seed situation first")
    mb.add_argument("--json", action="store_true")
    mw = msub.add_parser("watch", help="watch reports/memory/inbox")
    _mem_common(mw)
    mw.add_argument("--interval", type=int, default=5)
    ms = msub.add_parser("serve", help="HTTP API + watch + consolidate loop")
    _mem_common(ms)
    ms.add_argument("--port", type=int, default=8888)
    ms.add_argument("--consolidate-every", type=int, default=30)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Auto-announce upgrade/install for cwd (stderr) before the command runs.
    if update_check.should_auto_announce(args.command):
        update_check.announce(Path.cwd(), quiet_if_current=True)

    if args.command == "version":
        return version_cmd.run(
            as_json=bool(getattr(args, "json", False)),
            path=Path(getattr(args, "path", ".")).resolve(),
        )
    if args.command == "license":
        return license_cmd.run_check(getattr(args, "key", None))
    if args.command == "license-server":
        import os

        if args.host:
            os.environ["ORCHESTRATOR_LICENSE_SERVER_HOST"] = args.host
        if args.port is not None:
            os.environ["ORCHESTRATOR_LICENSE_SERVER_PORT"] = str(args.port)
        return license_server_mod.main([])
    if args.command == "status":
        target = Path(args.path).resolve()
        return status_cmd.run(target, as_json=args.json)
    if args.command == "check":
        target = Path(args.path).resolve()
        return check_cmd.run(
            target, as_json=args.json, quiet_ok=getattr(args, "quiet_ok", False)
        )
    if args.command == "init":
        target = Path(args.path).resolve()
        fg = getattr(args, "from_github", None)
        from_gh: str | bool | None = None
        if fg is not None:
            from_gh = True if fg == "latest" else fg
        return run_init(
            target,
            to_version=args.to,
            profile=args.profile,
            selections=args.selections,
            dry_run=args.dry_run,
            no_pr=args.no_pr,
            verify_bundle=getattr(args, "verify_bundle", False),
            from_github=from_gh,
            quiet=bool(getattr(args, "quiet", False)),
            stash=bool(getattr(args, "stash", False)),
        )
    if args.command == "upgrade":
        target = Path(args.path).resolve()
        fg = getattr(args, "from_github", None)
        from_gh: str | bool | None = None
        if fg is not None:
            from_gh = True if fg == "latest" else fg
        return run_upgrade(
            target,
            to_version=args.to,
            profile=args.profile,
            selections=args.selections,
            dry_run=args.dry_run,
            no_pr=args.no_pr,
            verify_bundle=getattr(args, "verify_bundle", False),
            if_available=bool(getattr(args, "if_available", False)),
            yes=bool(getattr(args, "yes", False)),
            from_github=from_gh,
            quiet=bool(getattr(args, "quiet", False)),
            stash=bool(getattr(args, "stash", False)),
        )
    if args.command == "self-upgrade":
        fg = getattr(args, "from_github", None)
        from_gh: str | bool | None = None
        if fg is not None:
            from_gh = True if fg == "latest" else fg
        return self_upgrade_cmd.run(
            to_version=getattr(args, "to", None),
            from_github=from_gh,
            method=str(getattr(args, "method", "auto") or "auto"),
            yes=bool(getattr(args, "yes", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
            as_json=bool(getattr(args, "json", False)),
        )
    if args.command == "memory":
        return memory_cmd.run(args)
    if args.command == "install-persist":
        target = Path(args.path).resolve()
        return install_persist_cmd.run(
            target,
            as_json=bool(getattr(args, "json", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    if args.command == "ensure":
        target = Path(args.path).resolve()
        only_mcp = bool(getattr(args, "mcp", False))
        only_tools = bool(getattr(args, "host_tools", False))
        # Default: host tools only. MCP is opt-in (--mcp). Product default MCP off.
        if only_mcp or only_tools:
            do_mcp, do_tools = only_mcp, only_tools
        else:
            do_mcp, do_tools = False, True
        return ensure_cmd.run(
            path=target,
            mcp=do_mcp,
            host_tools=do_tools,
            check=bool(getattr(args, "check", False)),
            force=bool(getattr(args, "force", False)),
            yes=bool(getattr(args, "yes", False)),
            quiet=bool(getattr(args, "quiet", False)),
            as_json=bool(getattr(args, "json", False)),
        )
    if args.command == "uninstall":
        target = Path(args.path).resolve()
        dry_run = not bool(getattr(args, "apply", False))
        do_host = bool(getattr(args, "host", False))
        # Project removal is default; --no-project for host-only; --host alone also does project unless --no-project
        do_project = not bool(getattr(args, "no_project", False))
        return uninstall_cmd.run(
            target,
            dry_run=dry_run,
            yes=bool(getattr(args, "yes", False)),
            host=do_host,
            project=do_project,
            selections=getattr(args, "selections", None),
            remove_cache=bool(getattr(args, "remove_cache", False)),
            remove_todo=bool(getattr(args, "remove_todo", False)),
            remove_state=bool(getattr(args, "remove_state", False)),
            remove_memories=bool(getattr(args, "remove_memories", False)),
            remove_manifests=bool(getattr(args, "remove_manifests", False)),
            force_template_source=bool(getattr(args, "force_template_source", False)),
            as_json=bool(getattr(args, "json", False)),
            npm=not bool(getattr(args, "no_npm", False)),
            pip=not bool(getattr(args, "no_pip", False)),
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())