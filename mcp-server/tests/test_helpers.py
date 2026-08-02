"""Unit tests for orchestrator MCP helpers."""

from pathlib import Path

from orchestrator_mcp.helpers import extract_open_todo_items, match_chains_by_intent


def test_extract_open_todo_items():
    text = """
## Open
- [ ] First task
- [x] Done task
- [ ] Second task
"""
    items = extract_open_todo_items(text, max_items=5)
    assert items == ["First task", "Second task"]


def test_match_chains_session_start():
    registry = {
        "chains": [
            {
                "id": "session-start",
                "intents": ["session start", "daily", "standup"],
            },
            {"id": "delivery", "intents": ["commit", "push"]},
        ]
    }
    matches = match_chains_by_intent(registry, "start session")
    assert matches[0]["id"] == "session-start"


def test_latest_todo_from_repo():
    root = Path(__file__).resolve().parents[2]
    from orchestrator_mcp.helpers import latest_todo_file

    todo = latest_todo_file(root)
    assert todo is not None
    assert todo.suffix == ".md"