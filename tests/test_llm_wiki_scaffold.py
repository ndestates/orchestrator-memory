"""Phase 1 tests for LLM Wiki scaffold (Karpathy pattern).

Pins: required tree, index/log presence, parseable log prefixes,
wiki_policy mode lean on template, no secrets in pilot raw/wiki samples.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WIKI = REPO_ROOT / "wiki"
RAW = REPO_ROOT / "raw"
MANIFEST = REPO_ROOT / ".github" / "project-manifest.yaml"
SKILL = REPO_ROOT / ".grok" / "skills" / "llm-wiki" / "SKILL.md"
SCHEMA = REPO_ROOT / ".grok" / "skills" / "llm-wiki" / "references" / "wiki-schema.md"

LOG_ENTRY = re.compile(
    r"^## \[(\d{4}-\d{2}-\d{2})\] (ingest|query|lint|scaffold|file-answer) \| .+"
)

REQUIRED_WIKI = [
    "index.md",
    "log.md",
    "contradictions.md",
    "open-questions.md",
    "sources/karpathy-llm-wiki.md",
    "sources/knowledge-vault.md",
    "concepts/compound-knowledge.md",
    "concepts/three-layer-architecture.md",
    "entities/orchestrator-knowledge-surfaces.md",
    "decisions/D1-scope-order.md",
]

REQUIRED_RAW = [
    "README.md",
    "research/2026-07-15-karpathy-llm-wiki.md",
    "evidence/2026-07-15-knowledge-vault-guide-snapshot.md",
]

SECRETISH = re.compile(
    r"(?i)(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|"
    r"-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----|"
    r"(api[_-]?key|password)\s*[:=]\s*['\"][^'\"]{12,})"
)


def test_skill_and_schema_exist():
    assert SKILL.is_file()
    assert SCHEMA.is_file()
    text = SKILL.read_text(encoding="utf-8")
    assert "compress-or-skip" in text or "compress_or_skip" in text
    assert "wiki_policy" in text


def test_wiki_tree_required_files():
    for rel in REQUIRED_WIKI:
        assert (WIKI / rel).is_file(), f"missing wiki/{rel}"


def test_raw_tree_required_files():
    for rel in REQUIRED_RAW:
        assert (RAW / rel).is_file(), f"missing raw/{rel}"


def test_log_has_parseable_entries():
    log = (WIKI / "log.md").read_text(encoding="utf-8")
    entries = [ln for ln in log.splitlines() if ln.startswith("## [")]
    assert len(entries) >= 2, "expected pilot scaffold + ingest log lines"
    for ln in entries:
        assert LOG_ENTRY.match(ln), f"bad log prefix: {ln}"


def test_index_lists_pilot_pages():
    idx = (WIKI / "index.md").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki" in idx
    assert "knowledge-vault" in idx
    assert "compound-knowledge" in idx


def test_manifest_wiki_policy_lean():
    text = MANIFEST.read_text(encoding="utf-8")
    assert "wiki_policy:" in text
    assert 'mode: "lean"' in text or "mode: 'lean'" in text
    assert "auto_ingest: false" in text
    assert "require_approval_for_writes: true" in text
    assert 'wiki_dir: "wiki"' in text


def test_registry_has_wiki_skill_and_chains():
    reg = (REPO_ROOT / "chains" / "registry.yaml").read_text(encoding="utf-8")
    assert "- id: llm-wiki" in reg
    assert "- id: wiki-ingest" in reg
    assert "- id: wiki-query" in reg
    assert "- id: wiki-lint" in reg


def test_pilot_content_has_no_secret_patterns():
    paths = list(WIKI.rglob("*.md")) + list(RAW.rglob("*.md"))
    assert paths
    for p in paths:
        body = p.read_text(encoding="utf-8", errors="replace")
        m = SECRETISH.search(body)
        assert m is None, f"secret-like pattern in {p}: {m.group(0)[:40] if m else ''}"


def test_deploy_bundle_has_wiki_selection():
    bundle = (REPO_ROOT / "scripts" / "deploy-bundle.yaml").read_text(encoding="utf-8")
    assert re.search(r"(?m)^  wiki:", bundle)
    assert "wiki/index.md" in bundle or ".grok/skills/llm-wiki" in bundle
    assert "session-wiki-brief.py" in bundle


def test_session_wiki_brief_ok():
    import importlib.util

    path = REPO_ROOT / "scripts" / "session-wiki-brief.py"
    spec = importlib.util.spec_from_file_location("session_wiki_brief", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    brief = mod.build_brief(REPO_ROOT)
    assert brief["status"] == "ok"
    assert brief["mode"] == "lean"
    assert brief.get("log_tail")


def test_wiki_lint_check_ok():
    import importlib.util

    path = REPO_ROOT / "scripts" / "wiki_lint_check.py"
    spec = importlib.util.spec_from_file_location("wiki_lint_check", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    result = mod.lint(REPO_ROOT)
    assert result["status"] in ("ok", "warn"), result
    assert result["mode"] == "lean"


def test_mcp_sandbox_allows_wiki_and_raw():
    from orchestrator_mcp.sandbox import assert_readable, ALLOWED_READ_PREFIXES

    assert "wiki" in ALLOWED_READ_PREFIXES
    assert "raw" in ALLOWED_READ_PREFIXES
    assert_readable(REPO_ROOT, "wiki/index.md")
    assert_readable(REPO_ROOT, "raw/README.md")


def test_registry_has_wiki_lint_watch_and_session_wiki():
    reg = (REPO_ROOT / "chains" / "registry.yaml").read_text(encoding="utf-8")
    assert "- id: wiki-lint-watch" in reg
    assert "session-wiki-brief" in reg or "id: wiki-brief" in reg
