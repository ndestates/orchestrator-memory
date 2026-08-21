"""Map always-on memory roles onto project agents (all registered specialists).

Inventory comes from chains/registry.yaml skills + .grok/agents + .claude/agents.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# Memory specialist roles (Google pattern) → preferred project agents
MEMORY_ROLE_AGENTS: dict[str, list[str]] = {
    "ingest": [
        "documentation-specialist",
        "readme-specialist",
        "todo-specialist-agent",
        "changelog-specialist",
    ],
    "consolidate": [
        "loop-compound",
        "loop-verifier",
        "project-drift-guardian",
        "cache-efficient",
    ],
    "query": [
        "orchestrator",
        "branch-context-agent",
        "todo-specialist-agent",
        "daily-standup-with-cache",
        "session-resume",
    ],
    "query_security": [
        "security-audit-agent",
        "cyber-security-essentials",
        "bug-hunter-agent",
    ],
    "query_schema": [
        "schema-audit-agent",
        "data-architect-expert",
        "mysql-database-expert",
        "mariadb-database-expert",
        "sqlite-database-expert",
    ],
    "query_code": [
        "bug-hunter-agent",
        "code-review",
        "python-expert",
        "laravel-expert-agent",
        "frontend-web-design-expert",
    ],
    "daemon": [
        "session-context-envelope",
        "token-usage-meter",
        "model-route",
    ],
}


def discover_agents(root: Path | None = None) -> list[dict[str, Any]]:
    """List all agents/skills known to this project."""
    root = root or ROOT
    found: dict[str, dict[str, Any]] = {}

    reg = root / "chains" / "registry.yaml"
    if reg.is_file():
        text = reg.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(
            r"(?m)^- id:\s*([a-zA-Z0-9_-]+)\s*\n(?:  .*\n)*?  path:\s*(.+)$",
            text,
        ):
            aid = m.group(1).strip()
            path = m.group(2).strip()
            found[aid] = {"id": aid, "source": "registry", "path": path}

        # also plain skill ids without path capture fallback
        for m in re.finditer(r"(?m)^- id:\s*([a-zA-Z0-9_-]+)\s*$", text):
            aid = m.group(1).strip()
            if aid not in found:
                found[aid] = {"id": aid, "source": "registry", "path": ""}

    for agents_dir, source in (
        (root / ".grok" / "agents", "grok_agents"),
        (root / ".claude" / "agents", "claude_agents"),
        (root / ".grok" / "skills", "grok_skills"),
    ):
        if not agents_dir.is_dir():
            continue
        for p in agents_dir.iterdir():
            if p.suffix == ".md":
                aid = p.stem
                found.setdefault(
                    aid, {"id": aid, "source": source, "path": str(p.relative_to(root))}
                )
            elif p.is_dir() and (p / "SKILL.md").is_file():
                aid = p.name
                found.setdefault(
                    aid,
                    {
                        "id": aid,
                        "source": source,
                        "path": str((p / "SKILL.md").relative_to(root)),
                    },
                )

    return sorted(found.values(), key=lambda x: x["id"])


def pick_agent_for_role(
    role: str,
    *,
    root: Path | None = None,
    question: str = "",
) -> dict[str, Any]:
    """Select primary + fallback agents for a memory role."""
    root = root or ROOT
    inventory = {a["id"]: a for a in discover_agents(root)}
    q = (question or "").lower()

    # Dynamic override from question keywords
    role_key = role
    if role == "query":
        if any(k in q for k in ("security", "secret", "cve", "auth", "threat")):
            role_key = "query_security"
        elif any(k in q for k in ("schema", "migration", "database", "sql")):
            role_key = "query_schema"
        elif any(k in q for k in ("bug", "code", "implement", "refactor")):
            role_key = "query_code"

    preferred = MEMORY_ROLE_AGENTS.get(role_key) or MEMORY_ROLE_AGENTS.get(role) or [
        "orchestrator"
    ]
    chosen: list[dict[str, Any]] = []
    for pid in preferred:
        if pid in inventory:
            chosen.append({**inventory[pid], "preferred": True})
        else:
            chosen.append({"id": pid, "source": "role_map", "path": "", "preferred": True})

    # Attach a sample of *all* other agents so the system knows full roster
    others = [a for a in inventory.values() if a["id"] not in {c["id"] for c in chosen}]
    return {
        "role": role_key,
        "primary": chosen[0]["id"] if chosen else "orchestrator",
        "agents": chosen,
        "roster_size": len(inventory),
        "roster_sample": [a["id"] for a in others[:20]],
        "roster_all_ids": sorted(inventory.keys()),
    }


def agents_inventory_brief(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    agents = discover_agents(root)
    return {
        "count": len(agents),
        "agents": agents,
        "role_picks": {
            role: pick_agent_for_role(role, root=root)["primary"]
            for role in MEMORY_ROLE_AGENTS
        },
    }
