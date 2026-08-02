"""Host CLI: orchestrator memory …"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from orchestrator_cli.commands import memory as memory_cmd
from orchestrator_cli import __main__ as main_mod


def test_resolve_project_root_cwd():
    root = memory_cmd.resolve_project_root(".")
    assert root.is_dir()


def test_memory_db_paths():
    p = Path(tempfile.mkdtemp())
    assert memory_cmd.memory_db_for(p, scope="project") == p / "reports" / "memory" / "memory.db"
    g = memory_cmd.memory_db_for(p, scope="global")
    assert "memory" in str(g)


def test_memory_ingest_and_query_via_cli(tmp_path: Path | None = None):
    root = Path(tempfile.mkdtemp())
    (root / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (root / "TODO").mkdir()
    (root / "TODO" / "t.md").write_text("# TODO\n- [ ] open work\n", encoding="utf-8")
    code = memory_cmd.run_memory_argv(
        ["ingest", "--text", "Host CLI memory 2.0.0 works", "--source", "test"],
        project=root,
        scope="project",
    )
    assert code == 0
    code = memory_cmd.run_memory_argv(
        ["query", "Host CLI memory"],
        project=root,
        scope="project",
    )
    assert code == 0
    code = memory_cmd.run_memory_argv(["status"], project=root, scope="project")
    assert code == 0


def test_memory_brief():
    root = Path(tempfile.mkdtemp())
    (root / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (root / "TODO").mkdir()
    code = memory_cmd.run_brief(project=root, seed=True, as_json=False)
    assert code == 0


def test_parser_has_memory():
    p = main_mod.build_parser()
    args = p.parse_args(["memory", "status", "--path", "."])
    assert args.command == "memory"
    assert args.memory_command == "status"


def test_main_memory_status():
    # Uses real template root / cwd — should not crash
    rc = main_mod.main(["memory", "db-path", "--path", "."])
    assert rc == 0


if __name__ == "__main__":
    test_resolve_project_root_cwd()
    test_memory_db_paths()
    test_memory_ingest_and_query_via_cli()
    test_memory_brief()
    test_parser_has_memory()
    test_main_memory_status()
    print("all cli memory tests passed")
