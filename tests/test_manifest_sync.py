"""Per-platform project-manifest sync."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from _engine import manifest_sync as ms


def test_extract_manifest_body_skips_comments():
    text = "# header\n\nproject:\n  name: x\n"
    assert ms.extract_manifest_body(text) == "project:\n  name: x\n"


def test_sync_manifests_writes_all_platforms(tmp_path):
    canonical = tmp_path / ".github" / "project-manifest.yaml"
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        ms.platform_header("GitHub Copilot (canonical — edit here)", canonical=True)
        + 'project:\n  name: "Test"\n',
        encoding="utf-8",
    )
    touched = ms.sync_manifests(tmp_path)
    assert len(touched) >= len(ms.MANIFEST_TARGETS) - 1
    for rel, _ in ms.MANIFEST_TARGETS:
        path = tmp_path / rel
        assert path.is_file(), rel
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["project"]["name"] == "Test"


def test_all_template_manifests_parse():
    root = Path(__file__).resolve().parents[1]
    for rel, _ in ms.MANIFEST_TARGETS:
        path = root / rel
        assert path.is_file(), f"missing {rel}"
        yaml.safe_load(path.read_text(encoding="utf-8"))


def test_template_manifest_bodies_match():
    root = Path(__file__).resolve().parents[1]
    bodies = {rel: ms.extract_manifest_body((root / rel).read_text(encoding="utf-8")) for rel, _ in ms.MANIFEST_TARGETS}
    canonical_body = bodies[ms.CANONICAL_REL]
    for rel, body in bodies.items():
        assert body == canonical_body, f"{rel} body drift from canonical"


def test_find_manifest_path_prefers_canonical_order(tmp_path):
    (tmp_path / ".grok").mkdir()
    (tmp_path / ".grok" / "project-manifest.yaml").write_text(
        "project:\n  name: grok\n", encoding="utf-8"
    )
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "project-manifest.yaml").write_text(
        "project:\n  name: github\n", encoding="utf-8"
    )
    found = ms.find_manifest_path(tmp_path)
    assert found == tmp_path / ".github" / "project-manifest.yaml"