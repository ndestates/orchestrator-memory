"""pre-commit auto-regen for bundle-hashes stamp (CI hygiene)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = REPO_ROOT / "scripts" / "orchestrator-bundle-hash.py"
    spec = importlib.util.spec_from_file_location("orch_bundle_hash", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pre_commit_noop_when_clean_and_no_high_risk_staged(tmp_path: Path, monkeypatch):
    m = _load()
    # Minimal tree
    (tmp_path / "scripts" / "security").mkdir(parents=True)
    (tmp_path / "reports" / "security").mkdir(parents=True)
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    sample = tmp_path / "scripts" / "sample.sh"
    sample.write_text("#!/bin/bash\necho ok\n", encoding="utf-8")
    paths = tmp_path / "scripts" / "security" / "bundle-paths.txt"
    paths.write_text("scripts/sample.sh\nVERSION\n", encoding="utf-8")
    specs = m.load_path_specs(paths)
    stamp = tmp_path / "reports" / "security" / "bundle-hashes.json"
    manifest = m.build_manifest(tmp_path, specs)
    m.write_stamp(manifest, stamp)

    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    # stage only a non-high-risk file
    other = tmp_path / "README.md"
    other.write_text("hi\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)

    before = stamp.read_text(encoding="utf-8")
    rc = m.run_pre_commit(tmp_path, specs, stamp, quiet=True)
    assert rc == 0
    assert stamp.read_text(encoding="utf-8") == before


def test_pre_commit_regens_when_high_risk_staged(tmp_path: Path, monkeypatch):
    m = _load()
    (tmp_path / "scripts" / "security").mkdir(parents=True)
    (tmp_path / "reports" / "security").mkdir(parents=True)
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    sample = tmp_path / "scripts" / "sample.sh"
    sample.write_text("#!/bin/bash\necho ok\n", encoding="utf-8")
    paths = tmp_path / "scripts" / "security" / "bundle-paths.txt"
    paths.write_text("scripts/sample.sh\nVERSION\n", encoding="utf-8")
    specs = m.load_path_specs(paths)
    stamp = tmp_path / "reports" / "security" / "bundle-hashes.json"
    m.write_stamp(m.build_manifest(tmp_path, specs), stamp)
    old_hash = m.build_manifest(tmp_path, specs)["bundle_hash"]

    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    # mutate high-risk file and stage it (stamp intentionally stale)
    sample.write_text("#!/bin/bash\necho changed\n", encoding="utf-8")
    subprocess.run(["git", "add", "scripts/sample.sh"], cwd=tmp_path, check=True)

    rc = m.run_pre_commit(tmp_path, specs, stamp, quiet=True)
    assert rc == 0
    new_hash = m.build_manifest(tmp_path, specs)["bundle_hash"]
    assert new_hash != old_hash
    # stamp staged
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        cwd=tmp_path,
        text=True,
    )
    assert "reports/security/bundle-hashes.json" in staged
    ok, issues, _ = m.verify(tmp_path, stamp, specs)
    assert ok, issues


def test_pre_commit_skip_env(tmp_path: Path, monkeypatch):
    m = _load()
    monkeypatch.setenv("ORCHESTRATOR_BUNDLE_HASH_SKIP", "1")
    assert m.run_pre_commit(tmp_path, [], tmp_path / "x.json", quiet=True) == 0
