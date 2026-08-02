"""Open-source first model-route catalog and suggestions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_mod():
    path = ROOT / "scripts" / "model-route-suggest.py"
    spec = importlib.util.spec_from_file_location("model_route_suggest", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_mod()


def test_catalog_has_open_weights():
    cat = mod.load_catalog()
    oss = mod.assert_oss_catalog(cat)
    assert len(oss) >= 1
    assert all(m.get("license") == "open_weights" for m in oss)


def test_low_tier_oss_ready_recommends_oss():
    cat = mod.load_catalog()
    s = mod.build_suggestion(
        root=ROOT,
        task="session-start status list",
        chain_id="session-start",
        platform="grok",
        catalog=cat,
        ollama_report={"ollama_api": "reachable", "ollama_model_names": ["llama3.2:3b"]},
        installed_models=["llama3.2:3b"],
    )
    assert s["demand"] == "low"
    assert s["offer"] is True
    assert str(s["recommend"]).startswith("oss:")
    assert "oss" in s["switch_options"]


def test_low_tier_oss_missing_install_offer():
    cat = mod.load_catalog()
    s = mod.build_suggestion(
        root=ROOT,
        task="todo brief",
        chain_id="session-start",
        platform="grok",
        catalog=cat,
        ollama_report={"ollama_api": "unreachable", "ollama_model_names": []},
        installed_models=[],
    )
    assert s["demand"] == "low"
    assert s["offer"] is True
    assert "install-oss" in str(s["recommend"]) or "install-oss" in s["switch_options"]


def test_high_security_stays():
    cat = mod.load_catalog()
    s = mod.build_suggestion(
        root=ROOT,
        task="security audit production secrets",
        chain_id="security-audit",
        platform="grok",
        catalog=cat,
        ollama_report={"ollama_api": "reachable", "ollama_model_names": ["llama3.2:3b"]},
        installed_models=["llama3.2:3b"],
    )
    assert s["demand"] == "high"
    assert s["recommend"] == "stay"
    assert s["offer"] is False
