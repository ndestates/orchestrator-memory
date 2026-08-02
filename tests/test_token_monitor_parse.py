"""Phase A BH-004: single-pass token_monitor updates.jsonl parse."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".grok/skills/token-usage-meter/scripts/token_monitor.py"
LIB = REPO / ".grok/skills/token-usage-meter/scripts"


def _load_monitor():
    sys.path.insert(0, str(LIB))
    spec = importlib.util.spec_from_file_location("token_monitor_phase_a", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_session_updates_single_read(tmp_path: Path, monkeypatch=None):
    m = _load_monitor()
    updates = tmp_path / "updates.jsonl"
    lines = []
    for i, tokens in enumerate([1000, 2500, 4000], start=1):
        # user chunk with model
        lines.append(
            json.dumps(
                {
                    "params": {
                        "update": {
                            "sessionUpdate": "user_message_chunk",
                            "content": {
                                "text": f"hello {i}",
                                "_meta": {"modelId": "test-model"},
                            },
                        },
                        "_meta": {"agentTimestampMs": i * 100, "turnStartMs": i * 100},
                    }
                }
            )
        )
        lines.append(
            json.dumps(
                {
                    "params": {
                        "update": {"sessionUpdate": "agent_message_chunk"},
                        "_meta": {
                            "turnStartMs": i * 100,
                            "totalTokens": tokens,
                        },
                    }
                }
            )
        )
    updates.write_text("\n".join(lines) + "\n", encoding="utf-8")

    reads = {"n": 0}
    orig = Path.read_text

    def counting_read(self, *a, **k):
        if self == updates or self.name == "updates.jsonl":
            reads["n"] += 1
        return orig(self, *a, **k)

    Path.read_text = counting_read  # type: ignore[method-assign]
    try:
        model, turns = m.parse_session_updates(updates)
    finally:
        Path.read_text = orig  # type: ignore[method-assign]

    assert model == "test-model"
    assert len(turns) == 3
    assert turns[-1]["context_tokens"] == 4000
    assert reads["n"] == 1


def test_wrappers_delegate_to_single_pass(tmp_path: Path):
    m = _load_monitor()
    updates = tmp_path / "updates.jsonl"
    updates.write_text(
        json.dumps(
            {
                "params": {
                    "update": {
                        "sessionUpdate": "user_message_chunk",
                        "content": {"text": "x", "_meta": {"modelId": "m1"}},
                    },
                    "_meta": {"turnStartMs": 1, "totalTokens": 50, "agentTimestampMs": 1},
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert m.parse_session_model_id(updates) == "m1"
    turns = m.parse_session_turns(updates)
    assert len(turns) == 1
    assert turns[0]["context_tokens"] == 50
