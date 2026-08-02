"""Phase 0 safety-net tests for scripts/deploy_grok_to_project.py.

These pin the current behavior of the pure/injectable functions so the Phase 2
refactor (parameterizing ROOT -> template_root) cannot silently regress them.
"""

from __future__ import annotations


def test_sha256_file_deterministic(deploy_mod, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello", encoding="utf-8")
    h1 = deploy_mod.sha256_file(f)
    h2 = deploy_mod.sha256_file(f)
    assert h1 == h2 and len(h1) == 64


def test_skip_artifact(deploy_mod, tmp_path):
    assert deploy_mod._skip_artifact(tmp_path / "x" / "__pycache__" / "m.pyc")
    assert deploy_mod._skip_artifact(tmp_path / "m.pyc")
    assert deploy_mod._skip_artifact(tmp_path / "m.pyo")
    assert not deploy_mod._skip_artifact(tmp_path / ".grok" / "skills" / "x" / "SKILL.md")


def test_load_state_defaults_and_roundtrip(deploy_mod, target):
    state = deploy_mod.load_state(target)
    assert "files" in state
    state["files"]["x"] = {"deployed_sha256": "abc"}
    state["version"] = "1.3.0"  # additive field tolerated
    deploy_mod.save_state(target, state)
    reloaded = deploy_mod.load_state(target)
    assert reloaded["files"]["x"]["deployed_sha256"] == "abc"
    assert reloaded["version"] == "1.3.0"


def test_deploy_file_new_copies_and_records(deploy_mod, target, stats):
    src = target.parent / "src.md"
    src.write_text("# template\n", encoding="utf-8")
    state = deploy_mod.load_state(target)
    deploy_mod.deploy_file(
        "docs/x.md", src, target, state,
        dry_run=False, default_action="skip", interactive=False,
        stats=stats, backup=None,
    )
    out = target / "docs" / "x.md"
    assert out.read_text(encoding="utf-8") == "# template\n"
    assert stats["new"] == 1
    assert state["files"]["docs/x.md"]["last_action"] == "new"


def test_deploy_quiet_suppresses_per_file_chatter(target, stats, capsys):
    """Engine deploy quiet mode must hide per-file NEW lines (agent-safe)."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    scripts = str(root / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from _engine import deploy as eng

    src = target.parent / "src.md"
    src.write_text("# template\n", encoding="utf-8")
    state = eng.load_state(target)
    prev = eng._QUIET
    eng._QUIET = True
    try:
        eng.deploy_file(
            "docs/quiet.md",
            src,
            target,
            state,
            dry_run=False,
            default_action="skip",
            interactive=False,
            stats=stats,
            backup=None,
        )
    finally:
        eng._QUIET = prev
    out = capsys.readouterr().out
    assert "NEW" not in out
    assert stats["new"] == 1
    assert (target / "docs" / "quiet.md").is_file()



def test_deploy_file_dry_run_writes_nothing(deploy_mod, target, stats):
    src = target.parent / "src.md"
    src.write_text("x", encoding="utf-8")
    state = deploy_mod.load_state(target)
    deploy_mod.deploy_file(
        "docs/x.md", src, target, state,
        dry_run=True, default_action="skip", interactive=False,
        stats=stats, backup=None,
    )
    assert not (target / "docs" / "x.md").exists()
    assert stats["new"] == 1  # counted, but not written


def test_deploy_file_customized_conflict_skipped(deploy_mod, target, stats):
    # Target file differs from template, no prior state -> first-seen conflict,
    # default-action skip must preserve the local content.
    rel = "docs/x.md"
    (target / "docs").mkdir(parents=True)
    (target / rel).write_text("LOCAL EDIT\n", encoding="utf-8")
    src = target.parent / "src.md"
    src.write_text("TEMPLATE\n", encoding="utf-8")
    state = deploy_mod.load_state(target)
    deploy_mod.deploy_file(
        rel, src, target, state,
        dry_run=False, default_action="skip", interactive=False,
        stats=stats, backup=None,
    )
    assert (target / rel).read_text(encoding="utf-8") == "LOCAL EDIT\n"
    assert stats["conflict"] == 1
    assert stats["overwritten"] == 0


def test_resolve_selections_all_and_default(deploy_mod):
    bundle = {
        "default_selections": ["grok", "chains"],
        "selections": {"grok": {}, "chains": {}, "scripts": {}},
    }
    assert set(deploy_mod.resolve_selections(bundle, "all")) == {"grok", "chains", "scripts"}
    assert deploy_mod.resolve_selections(bundle, None) == ["grok", "chains"]
    assert deploy_mod.resolve_selections(bundle, "grok,scripts") == ["grok", "scripts"]


def test_scripts_selection_includes_multi_workstream_runtime():
    """Default upgrade (scripts selection) must ship multi-workstream CLIs.

    Apps invoke python3 scripts/workstream*.py via /multi-workstream; missing
    from deploy-bundle.yaml means opt-in pre-release upgrades install the skill
    but not the runtime.
    """
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[1]
    bundle = yaml.safe_load((root / "scripts" / "deploy-bundle.yaml").read_text(encoding="utf-8"))
    files = set(bundle["selections"]["scripts"].get("files") or [])
    required = {
        "scripts/workstream.py",
        "scripts/workstream_worktree.py",
        "scripts/workstream_guard.py",
        "scripts/workstream_prompts.py",
        "scripts/workstream_recommend.py",
        "scripts/workstream_graph_example.py",
        "scripts/sync-multi-workstream-surfaces.py",
        "reports/sessions/workstreams.example.yaml",
    }
    missing = sorted(required - files)
    assert not missing, f"deploy-bundle scripts selection missing: {missing}"
    for rel in required:
        assert (root / rel).is_file(), f"source missing for deploy entry: {rel}"
