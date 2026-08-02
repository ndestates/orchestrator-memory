"""Full test suite for always-on memory agent (store, models, agents, LLM, CLI, brief).

Layout under test:
  scripts/memory_agent.py              CLI + HTTP + watch
  scripts/session-memory-brief.py      session-start brief
  scripts/_engine/memory_store.py      SQLite
  scripts/_engine/memory_models.py     full model-route catalog routing
  scripts/_engine/memory_agents.py     full agent roster routing
  scripts/_engine/memory_llm.py        Ollama + heuristic backends
  reports/memory/memory.db             runtime store (gitignored)
  reports/memory/inbox/                drop folder
  .grok/skills/always-on-memory/       skill surface
  docs/guides/always-on-memory.md      guide

Runnable:
  python3 tests/test_memory_agent.py
  python3 -m pytest tests/test_memory_agent.py -q   # when pytest installed
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from _engine import memory_agents as magents  # noqa: E402
from _engine import memory_llm as mllm  # noqa: E402
from _engine import memory_models as mmodels  # noqa: E402
from _engine import memory_store as mstore  # noqa: E402


# ── helpers ────────────────────────────────────────────────────


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cli():
    return _load("memory_agent_cli", ROOT / "scripts" / "memory_agent.py")


def _brief_mod():
    return _load("session_memory_brief", ROOT / "scripts" / "session-memory-brief.py")


def _tmp_root() -> Path:
    """Isolated mini project root for CLI/store tests."""
    root = Path(tempfile.mkdtemp(prefix="mem-test-"))
    (root / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (root / "TODO").mkdir()
    (root / "TODO" / "2026-07-31_TODO.md").write_text(
        "# TODO — 2.0.0\n\n1. [ ] **P1** App upgrades to **v2.0.0** carefully\n"
        "2. [ ] Optional: host install page\n",
        encoding="utf-8",
    )
    (root / "reports" / "memory" / "inbox").mkdir(parents=True)
    (root / "reports" / "sessions").mkdir(parents=True)
    (root / "reports" / "sessions" / "resume-2026-07-31.md").write_text(
        "Orchestrator — resume\nVer: 2.0.0\nOpen: P1 app upgrades\n",
        encoding="utf-8",
    )
    (root / "scripts" / "model-route").mkdir(parents=True)
    cat = (ROOT / "scripts" / "model-route" / "catalog.yaml").read_text(encoding="utf-8")
    (root / "scripts" / "model-route" / "catalog.yaml").write_text(cat, encoding="utf-8")
    (root / "chains").mkdir()
    (root / "chains" / "registry.yaml").write_text(
        "- id: orchestrator\n  path: x\n"
        "- id: documentation-specialist\n  path: y\n"
        "- id: todo-specialist-agent\n  path: z\n"
        "- id: loop-compound\n  path: a\n"
        "- id: security-audit-agent\n  path: b\n"
        "- id: schema-audit-agent\n  path: c\n"
        "- id: bug-hunter-agent\n  path: d\n"
        "- id: session-context-envelope\n  path: e\n",
        encoding="utf-8",
    )
    (root / ".grok" / "agents").mkdir(parents=True)
    (root / ".grok" / "agents" / "python-expert.md").write_text("# py\n", encoding="utf-8")
    return root


# ── store ──────────────────────────────────────────────────────


def test_store_roundtrip():
    db = Path(tempfile.mkdtemp()) / "memory.db"
    r = mstore.store_memory(
        db,
        raw_text="VERSION=2.0.0 on master",
        summary="Template is 2.0.0 on master",
        entities=["orchestrator", "master"],
        topics=["version", "branch"],
        importance=0.9,
        source="test",
        agent_id="todo-specialist-agent",
        model_id="heuristic",
    )
    assert r["memory_id"] >= 1
    mems = mstore.read_memories(db)["memories"]
    assert len(mems) == 1
    assert "2.0.0" in mems[0]["summary"]
    assert mems[0]["agent_id"] == "todo-specialist-agent"

    r2 = mstore.store_memory(
        db,
        raw_text="App upgrades carefully to 2.0.0",
        summary="P1 app upgrades to 2.0.0",
        entities=["apps"],
        topics=["upgrade"],
        importance=0.8,
        source="todo",
    )
    cons = mstore.store_consolidation(
        db,
        source_ids=[r["memory_id"], r2["memory_id"]],
        summary="Version and upgrades",
        insight="Ship app upgrades on 2.0.0 carefully",
        connections=[
            {
                "from_id": r["memory_id"],
                "to_id": r2["memory_id"],
                "relationship": "version_to_upgrade",
            }
        ],
        agent_id="loop-compound",
        model_id="heuristic",
    )
    assert cons["status"] == "consolidated"
    stats = mstore.get_stats(db)
    assert stats["total_memories"] == 2
    assert stats["unconsolidated"] == 0
    assert stats["consolidations"] == 1
    hist = mstore.read_consolidations(db)["consolidations"]
    assert hist[0]["insight"].startswith("Ship")


def test_store_delete_and_clear():
    db = Path(tempfile.mkdtemp()) / "m.db"
    a = mstore.store_memory(
        db, raw_text="a", summary="A", entities=[], topics=["t"], importance=0.5
    )
    b = mstore.store_memory(
        db, raw_text="b", summary="B", entities=[], topics=["t"], importance=0.5
    )
    assert mstore.delete_memory(db, a["memory_id"])["status"] == "deleted"
    assert mstore.delete_memory(db, 99999)["status"] == "not_found"
    assert mstore.get_stats(db)["total_memories"] == 1
    cleared = mstore.clear_all(db)
    assert cleared["memories_deleted"] == 1
    assert mstore.get_stats(db)["total_memories"] == 0


def test_store_processed_files():
    db = Path(tempfile.mkdtemp()) / "m.db"
    assert not mstore.is_file_processed(db, "/tmp/x.md")
    mstore.mark_file_processed(db, "/tmp/x.md")
    assert mstore.is_file_processed(db, "/tmp/x.md")


def test_store_unconsolidated_filter():
    db = Path(tempfile.mkdtemp()) / "m.db"
    m1 = mstore.store_memory(
        db, raw_text="1", summary="one", entities=[], topics=[], importance=0.5
    )
    m2 = mstore.store_memory(
        db, raw_text="2", summary="two", entities=[], topics=[], importance=0.5
    )
    un = mstore.read_memories(db, unconsolidated_only=True)["memories"]
    assert len(un) == 2
    mstore.store_consolidation(
        db,
        source_ids=[m1["memory_id"], m2["memory_id"]],
        summary="s",
        insight="i",
        connections=[],
    )
    un2 = mstore.read_memories(db, unconsolidated_only=True)["memories"]
    assert len(un2) == 0


def test_store_importance_clamped():
    db = Path(tempfile.mkdtemp()) / "m.db"
    r = mstore.store_memory(
        db,
        raw_text="x",
        summary="x",
        entities=[],
        topics=[],
        importance=5.0,
    )
    mem = mstore.read_memories(db)["memories"][0]
    assert 0.0 <= mem["importance"] <= 1.0


# ── models ─────────────────────────────────────────────────────


def test_models_inventory_includes_all_kinds():
    inv = mmodels.models_inventory_brief(ROOT)
    assert inv["catalog_total"] >= 10
    assert inv["oss_count"] >= 1
    assert inv["free_cloud_count"] >= 1
    assert inv["frontier_count"] >= 1
    kinds = {m["kind"] for m in inv["models"]}
    assert "oss" in kinds
    assert "free_cloud" in kinds
    assert "frontier" in kinds
    for role in ("ingest", "consolidate", "query", "query_status", "query_security"):
        pick = inv["picks"][role]
        assert pick.get("id"), f"missing pick for {role}"


def test_models_list_all_has_expected_surfaces():
    all_m = mmodels.list_all_models()
    ids = {m["id"] for m in all_m}
    assert any("llama" in i for i in ids)
    assert "gemini-flash" in ids or any("gemini" in i for i in ids)
    assert any(i.startswith("frontier:") for i in ids)


def test_pick_model_force_env(monkeypatch_env=None):
    os.environ["ORCHESTRATOR_MEMORY_MODEL"] = "llama3.2:3b"
    try:
        pick = mmodels.pick_model_for_role("ingest", root=ROOT)
        assert pick["id"] == "llama3.2:3b"
        assert pick["status"] in ("forced", "forced_unknown", "ready", "install_needed")
    finally:
        os.environ.pop("ORCHESTRATOR_MEMORY_MODEL", None)


def test_pick_model_high_security_prefers_frontier_or_oss():
    pick = mmodels.pick_model_for_role("query_security", root=ROOT)
    assert pick["demand"] == "high"
    # Without Ollama: interactive frontier; with Ollama may be oss ready
    assert pick["backend"] in ("host_agent", "ollama", "heuristic")


def test_role_demand_map():
    assert mmodels.ROLE_DEMAND["ingest"] == "low"
    assert mmodels.ROLE_DEMAND["consolidate"] == "medium"
    assert mmodels.ROLE_DEMAND["query_security"] == "high"


# ── agents ─────────────────────────────────────────────────────


def test_agents_inventory_nonempty():
    inv = magents.agents_inventory_brief(ROOT)
    assert inv["count"] >= 10
    assert inv["role_picks"]["ingest"]
    assert inv["role_picks"]["query"]
    assert inv["role_picks"]["consolidate"]


def test_agent_security_routing():
    pick = magents.pick_agent_for_role(
        "query", root=ROOT, question="security secrets audit threat"
    )
    assert pick["role"] == "query_security"
    assert "security" in pick["primary"] or pick["primary"] == "security-audit-agent"


def test_agent_schema_and_code_routing():
    schema = magents.pick_agent_for_role(
        "query", root=ROOT, question="database schema migration sql"
    )
    assert schema["role"] == "query_schema"
    code = magents.pick_agent_for_role(
        "query", root=ROOT, question="bug in code implement refactor"
    )
    assert code["role"] == "query_code"


def test_discover_agents_includes_files():
    agents = magents.discover_agents(ROOT)
    ids = {a["id"] for a in agents}
    assert "always-on-memory" in ids or len(ids) > 50
    assert any(a.get("source") for a in agents)


# ── llm / heuristic ────────────────────────────────────────────


def test_heuristic_ingest_multiline():
    text = "VERSION=2.0.0\nbranch=master\nP1 app upgrades"
    out = mllm.heuristic_ingest(text, source="seed")
    assert "2.0.0" in out["summary"]
    assert "branch=master" in out["summary"] or "VERSION" in out["summary"]
    assert out["importance"] >= 0.0


def test_heuristic_ingest_and_query():
    db = Path(tempfile.mkdtemp()) / "m.db"
    extracted = mllm.heuristic_ingest(
        "App upgrades to v2.0.0 carefully. MCP off by default.",
        source="todo",
    )
    assert extracted["summary"]
    mstore.store_memory(
        db,
        raw_text=extracted["raw_text"],
        summary=extracted["summary"],
        entities=extracted["entities"],
        topics=extracted["topics"],
        importance=extracted["importance"],
        source="todo",
    )
    mems = mstore.read_memories(db)["memories"]
    ans = mllm.heuristic_query("what about upgrades 2.0.0?", mems, [])
    assert "Memory" in ans or "upgrade" in ans.lower() or "2.0.0" in ans


def test_heuristic_consolidate_needs_two():
    one = mllm.heuristic_consolidate(
        [{"id": 1, "summary": "a", "topics": ["x"]}]
    )
    assert "Not enough" in one["summary"] or one["insight"] == ""
    two = mllm.heuristic_consolidate(
        [
            {"id": 1, "summary": "a", "topics": ["upgrade"]},
            {"id": 2, "summary": "b", "topics": ["version"]},
        ]
    )
    assert two["source_ids"] == [1, 2]
    assert two["connections"]


def test_extract_json_obj():
    assert mllm._extract_json_obj('{"a": 1}') == {"a": 1}
    assert mllm._extract_json_obj('noise {"b": 2} tail') == {"b": 2}
    assert mllm._extract_json_obj("not json") is None


def test_scrub_text_does_not_crash():
    out = mllm.scrub_text("hello world api_key=notreally")
    assert isinstance(out, str)


def test_llm_ingest_falls_back_heuristic():
    pick = {
        "id": "heuristic",
        "backend": "heuristic",
        "status": "fallback",
    }
    out = mllm.llm_ingest("Ship 2.0.0 memory agent", "test", pick)
    assert out["backend"] == "heuristic"
    assert out["summary"]


def test_llm_query_heuristic_path():
    pick = {"backend": "heuristic", "status": "fallback"}
    ans = mllm.llm_query(
        "anything?",
        [{"id": 1, "summary": "hello world project", "topics": ["general"], "raw_text": "hello"}],
        [],
        pick,
    )
    assert isinstance(ans, str)


# ── CLI ────────────────────────────────────────────────────────


def test_cli_status_models_agents():
    ma = _cli()
    # status prints JSON to stdout — capture via functions
    root = _tmp_root()
    # use engine paths relative to ROOT for catalog-heavy status is fine
    assert ma.cmd_status(ROOT) == 0
    assert ma.cmd_models(ROOT) == 0
    assert ma.cmd_agents(ROOT) == 0


def test_cli_ingest_query_consolidate():
    ma = _cli()
    root = _tmp_root()
    r = ma.do_ingest(root, "VERSION is 2.0.0 on master. P1 upgrades.", "test", dual_vault=False)
    assert r["status"] == "stored"
    assert r["agent"]
    assert r["model_pick"]["id"]
    r2 = ma.do_ingest(
        root,
        "Never multi-branch broadcast. Host package only.",
        "policy",
        dual_vault=False,
    )
    assert r2["memory_id"] != r["memory_id"]
    cons = ma.do_consolidate(root)
    assert cons["status"] in ("consolidated", "skipped")
    q = ma.do_query(root, "what version and upgrades?")
    assert q["memory_count"] >= 2
    assert "answer" in q
    assert q["agent"]


def test_cli_seed_situation():
    ma = _cli()
    root = _tmp_root()
    # seed uses git in root — may fail git bits but still stores VERSION/TODO
    result = ma.seed_situation(root)
    assert result.get("status") == "stored"
    assert "2.0.0" in str(result.get("summary", "")) or result.get("memory_id")


def test_cli_ingest_file_text_and_media_pointer():
    ma = _cli()
    root = _tmp_root()
    f = root / "reports" / "memory" / "inbox" / "note.md"
    f.write_text("Drop-folder note about 2.0.0 release\n", encoding="utf-8")
    r = ma.ingest_file(root, f)
    assert r["status"] == "stored"
    img = root / "reports" / "memory" / "inbox" / "shot.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\nnot-real")
    r2 = ma.ingest_file(root, img)
    assert r2["status"] == "stored"
    assert "multimodal" in r2.get("summary", "").lower() or "host" in r2.get("summary", "").lower()


def test_cli_watch_once():
    ma = _cli()
    root = _tmp_root()
    f = root / "reports" / "memory" / "inbox" / "w1.md"
    f.write_text("Watched file content for memory\n", encoding="utf-8")
    results = ma.watch_once(root)
    assert len(results) >= 1
    # second pass no re-ingest
    results2 = ma.watch_once(root)
    assert results2 == []


def test_cli_main_list_and_query_args():
    ma = _cli()
    root = _tmp_root()
    ma.do_ingest(root, "list test memory", "cli", dual_vault=False)
    assert ma.main(["--root", str(root), "list", "--limit", "5"]) == 0
    assert ma.main(["--root", str(root), "query", "list test"]) == 0
    assert ma.main(["--root", str(root), "status"]) == 0


def test_http_status_and_ingest_query():
    ma = _cli()
    root = _tmp_root()
    ma.do_ingest(root, "HTTP memory 2.0.0", "api", dual_vault=False)
    handler = ma._MemoryHandler
    handler.root = root
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        time.sleep(0.15)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as resp:
            stats = json.loads(resp.read().decode())
        assert stats["total_memories"] >= 1
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/query?q=HTTP+memory", timeout=5
        ) as resp:
            body = json.loads(resp.read().decode())
        assert "answer" in body
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/ingest",
            data=json.dumps({"text": "second via api", "source": "http"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            ing = json.loads(resp.read().decode())
        assert ing.get("status") == "stored"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/models", timeout=5) as resp:
            models = json.loads(resp.read().decode())
        assert models["catalog_total"] >= 1
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/agents", timeout=5) as resp:
            agents = json.loads(resp.read().decode())
        assert agents["count"] >= 1
    finally:
        server.shutdown()


# ── session brief ──────────────────────────────────────────────


def test_session_memory_brief_seeded():
    brief = _brief_mod()
    root = _tmp_root()
    ma = _cli()
    ma.do_ingest(root, "Brief test 2.0.0 open P1 upgrades", "seed", dual_vault=False)
    data = brief.build_brief(root, seed=False)
    assert data["status"] in ("ok", "empty")
    assert "stats" in data
    assert data["models_catalog_total"] >= 1
    assert data["picks"]["ingest_model"]
    assert data["situation"] is not None or data["stats"]["total_memories"] >= 0


def test_session_memory_brief_human_print():
    brief = _brief_mod()
    data = {
        "status": "ok",
        "stats": {"total_memories": 1, "unconsolidated": 0, "consolidations": 0},
        "models_catalog_total": 16,
        "oss_count": 5,
        "free_cloud_count": 5,
        "frontier_count": 6,
        "agents_count": 10,
        "picks": {
            "ingest_model": "llama3.2:3b",
            "ingest_agent": "documentation-specialist",
            "consolidate_model": "mistral",
            "consolidate_agent": "loop-compound",
            "query_model": "llama3.2:3b",
            "query_agent": "orchestrator",
        },
        "situation": "P1 upgrades",
        "insights": ["link A-B"],
    }
    brief.print_human(data)  # should not raise


# ── wiring / project integration ───────────────────────────────


def test_resume_branch_rejects_bare_origin():
    script = (ROOT / "scripts" / "resume-branch.sh").read_text(encoding="utf-8")
    assert "reject bare" in script or 'branch}" == "origin"' in script
    assert "origin/[^|]+" in script or "grep -E '^origin/" in script


def test_registry_has_memory_chain_and_session_step():
    reg = (ROOT / "chains" / "registry.yaml").read_text(encoding="utf-8")
    assert re.search(r"(?m)^- id: always-on-memory\s*$", reg)
    assert "session-memory-brief" in reg
    # session-start block contains memory-brief
    ss = reg.find("- id: session-start\n")
    assert ss != -1
    # next top-level chain after a reasonable window
    ne = reg.find("\n- id: template-deploy", ss)
    block = reg[ss : ne if ne != -1 else ss + 8000]
    assert "memory-brief" in block
    assert "always-on-memory" in block


def test_skill_and_guide_exist():
    skill = ROOT / ".grok" / "skills" / "always-on-memory" / "SKILL.md"
    guide = ROOT / "docs" / "guides" / "always-on-memory.md"
    assert skill.is_file()
    assert guide.is_file()
    text = skill.read_text(encoding="utf-8")
    m = re.search(r'description:\s*"([^"]+)"', text)
    assert m, "skill description required"
    assert len(m.group(1)) <= 220


def test_manifest_memory_paths_and_policy():
    man = (ROOT / ".github" / "project-manifest.yaml").read_text(encoding="utf-8")
    assert "memory_dir:" in man
    assert "memory_db:" in man
    assert "memory_inbox:" in man
    assert "memory_policy:" in man
    assert "use_full_model_catalog" in man
    assert "use_full_agent_roster" in man


def test_gitignore_memory_db():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "memory.db" in gi


def test_default_db_path():
    p = mstore.default_db_path(ROOT)
    assert p == ROOT / "reports" / "memory" / "memory.db"


def test_chain_md_lists_always_on_memory():
    chain = (ROOT / "CHAIN.md").read_text(encoding="utf-8")
    assert "always-on-memory" in chain


def test_stronger_with_every_update_standard_present():
    """Chrome-inspired security lifecycle is a product standard (2.0.0+)."""
    doc = ROOT / "docs" / "reference" / "stronger-with-every-update.md"
    sec = ROOT / "SECURITY.md"
    ref = ROOT / ".grok" / "references" / "stronger-with-every-update.md"
    assert doc.is_file(), "missing docs/reference/stronger-with-every-update.md"
    assert sec.is_file(), "missing root SECURITY.md trust map"
    assert ref.is_file(), "missing agent reference"
    body = doc.read_text(encoding="utf-8")
    assert "find" in body.lower() and "triage" in body.lower()
    assert "fix" in body.lower() and "apply" in body.lower()
    assert "blog.google/security/chrome-stronger-with-every-update" in body
    man = (ROOT / ".github" / "project-manifest.yaml").read_text(encoding="utf-8")
    assert "stronger_with_every_update: true" in man
    assert "security_md:" in man
    posture = (ROOT / "docs" / "internal" / "SECURITY-POSTURE.md").read_text(
        encoding="utf-8"
    )
    assert "Stronger with every update" in posture
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Stronger with every update" in claude


# ── runner ─────────────────────────────────────────────────────


def _run_all() -> int:
    tests = [
        v
        for k, v in sorted(globals().items())
        if k.startswith("test_") and callable(v)
    ]
    failed = 0
    for fn in tests:
        name = fn.__name__
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL  {name}: {exc}")
            import traceback

            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
