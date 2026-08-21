"""AI platform surface map — each model uses only its own tool tree.

Hard rule for every agent/session:
  Grok     → .grok/
  Claude   → .claude/
  Copilot  → .github/ + .copilot/  (canonical instructions under .github)
  Gemini   → .gemini/
  Cursor   → .cursor/
  ChatGPT  → .chatgpt/  (OpenAI ChatGPT / Codex / Agents — project-scoped)

Do not load another platform's skills/commands/agents as the primary procedure.
Shared project truth (TODO, docs/codebase, scripts/, reports/) is cross-platform.
"""

from __future__ import annotations

import os
from typing import Any

# Primary root for skills/commands/config the model must prefer
PLATFORM_SURFACES: dict[str, dict[str, Any]] = {
    "grok": {
        "id": "grok",
        "label": "Grok Build",
        "root": ".grok",
        "manifest": ".grok/project-manifest.yaml",
        "skills": ".grok/skills",
        "config": ".grok/config.toml",
        "mcp": ".grok/config.toml",
        "also_ok": [],
        "do_not_prefer": [".claude", ".copilot", ".gemini", ".cursor", ".chatgpt"],
    },
    "claude": {
        "id": "claude",
        "label": "Claude Code",
        "root": ".claude",
        "manifest": ".claude/project-manifest.yaml",
        "skills": ".claude/commands",  # Claude uses commands + agents
        "agents": ".claude/agents",
        "mcp": ".claude/mcp.claude.example.json",
        "also_ok": [],
        "do_not_prefer": [".grok", ".copilot", ".gemini", ".cursor", ".chatgpt"],
    },
    "copilot": {
        "id": "copilot",
        "label": "GitHub Copilot",
        "root": ".github",
        "manifest": ".github/project-manifest.yaml",
        "skills": ".github/skills",
        "instructions": ".github/copilot-instructions.md",
        "mcp": "mcp-server/config/mcp.copilot.vscode.example.json",
        "also_ok": [".copilot"],  # workspace mirror
        "do_not_prefer": [".grok", ".claude", ".gemini", ".cursor", ".chatgpt"],
    },
    "gemini": {
        "id": "gemini",
        "label": "Google Gemini",
        "root": ".gemini",
        "manifest": ".gemini/project-manifest.yaml",
        "skills": ".gemini/prompts",
        "instructions": ".gemini/instructions",
        "mcp": ".gemini/mcp.gemini.example.json",
        "also_ok": [],
        "do_not_prefer": [".grok", ".claude", ".copilot", ".cursor", ".chatgpt"],
    },
    "cursor": {
        "id": "cursor",
        "label": "Cursor IDE",
        "root": ".cursor",
        "manifest": ".cursor/project-manifest.yaml",
        "skills": ".cursor/rules",
        "config": ".cursor/mcp.json",
        "mcp": ".cursor/mcp.json",
        "also_ok": [],
        "do_not_prefer": [".grok", ".claude", ".copilot", ".gemini", ".chatgpt"],
    },
    "chatgpt": {
        "id": "chatgpt",
        "label": "ChatGPT / OpenAI (Codex, Agents)",
        "root": ".chatgpt",
        "manifest": ".chatgpt/project-manifest.yaml",
        "skills": ".chatgpt/prompts",
        "instructions": ".chatgpt/instructions",
        "mcp": ".chatgpt/mcp.chatgpt.example.json",
        "also_ok": [],
        "do_not_prefer": [".grok", ".claude", ".copilot", ".gemini", ".cursor"],
    },
}

# Shared paths every platform may use (not "another model's skill tree")
SHARED_PATHS = (
    "TODO/",
    "docs/codebase/",
    "docs/reference/",
    "docs/guides/",
    "scripts/",
    "reports/",
    "STATE.md",
    "VISION.md",
    "LOOP.md",
    "CHAIN.md",
    "chains/",
    "wiki/",
    "mcp-server/",
    "VERSION",
)

# Env signals → platform id (first match wins)
_ENV_HINTS: tuple[tuple[str, str], ...] = (
    ("GROK_AGENT", "grok"),
    ("GROK_SESSION_ID", "grok"),
    ("GROK_BUILD", "grok"),
    ("XAI_GROK", "grok"),
    ("CLAUDE_CODE", "claude"),
    ("CLAUDECODE", "claude"),
    ("ANTHROPIC_CLAUDE_CODE", "claude"),
    ("CURSOR_TRACE_ID", "cursor"),
    ("CURSOR_AGENT", "cursor"),
    ("GEMINI_CLI", "gemini"),
    ("GOOGLE_GENAI", "gemini"),
    ("COPILOT_AGENT", "copilot"),
    ("GITHUB_COPILOT", "copilot"),
    ("OPENAI_CHATGPT", "chatgpt"),
    ("CHATGPT_CODEX", "chatgpt"),
    ("CODEX_HOME", "chatgpt"),
    ("OPENAI_API_KEY", "chatgpt"),  # weak; only if no stronger host signal
)


def detect_platform(environ: dict[str, str] | None = None) -> str:
    """Best-effort platform id; prefer ORCHESTRATOR_AI_PLATFORM when set."""
    env = environ if environ is not None else dict(os.environ)
    explicit = (env.get("ORCHESTRATOR_AI_PLATFORM") or "").strip().lower()
    if explicit in PLATFORM_SURFACES:
        return explicit
    # aliases
    aliases = {
        "grok-build": "grok",
        "claude-code": "claude",
        "github": "copilot",
        "github-copilot": "copilot",
        "vs-code": "copilot",
        "vscode": "copilot",
        "openai": "chatgpt",
        "chat-gpt": "chatgpt",
        "codex": "chatgpt",
        "openai-codex": "chatgpt",
        "gpt": "chatgpt",
    }
    if explicit in aliases:
        return aliases[explicit]
    # Prefer strong host signals before weak OPENAI_API_KEY
    strong = (
        "GROK_AGENT",
        "GROK_SESSION_ID",
        "GROK_BUILD",
        "XAI_GROK",
        "CLAUDE_CODE",
        "CLAUDECODE",
        "ANTHROPIC_CLAUDE_CODE",
        "CURSOR_TRACE_ID",
        "CURSOR_AGENT",
        "GEMINI_CLI",
        "GOOGLE_GENAI",
        "COPILOT_AGENT",
        "GITHUB_COPILOT",
        "OPENAI_CHATGPT",
        "CHATGPT_CODEX",
        "CODEX_HOME",
    )
    for key in strong:
        if env.get(key):
            for hint_key, plat in _ENV_HINTS:
                if hint_key == key:
                    return plat
    # Weak API-key signal last (many hosts set OPENAI_API_KEY without being ChatGPT)
    if env.get("ORCHESTRATOR_AI_PLATFORM") == "" and env.get("OPENAI_API_KEY") and not any(
        env.get(k) for k in strong
    ):
        # Do not auto-claim chatgpt from OPENAI_API_KEY alone — too noisy
        pass
    for key, plat in _ENV_HINTS:
        if key == "OPENAI_API_KEY":
            continue
        if env.get(key):
            return plat
    return "unknown"


def surface_for(platform_id: str) -> dict[str, Any]:
    if platform_id in PLATFORM_SURFACES:
        return dict(PLATFORM_SURFACES[platform_id])
    return {
        "id": "unknown",
        "label": (
            "Unknown (set ORCHESTRATOR_AI_PLATFORM="
            "grok|claude|copilot|gemini|cursor|chatgpt)"
        ),
        "root": (
            "(detect your host: Grok→.grok Claude→.claude Copilot→.github "
            "Cursor→.cursor Gemini→.gemini ChatGPT→.chatgpt)"
        ),
        "manifest": ".github/project-manifest.yaml",
        "also_ok": [],
        "do_not_prefer": [],
        "rule": (
            "Identify your host product and use ONLY that surface for skills/commands; "
            "shared project paths are OK"
        ),
    }


def platform_brief(environ: dict[str, str] | None = None) -> dict[str, Any]:
    pid = detect_platform(environ)
    surf = surface_for(pid)
    return {
        "platform": pid,
        "surface_root": surf.get("root"),
        "surface_manifest": surf.get("manifest"),
        "surface_label": surf.get("label"),
        "also_ok": list(surf.get("also_ok") or []),
        "do_not_prefer": list(surf.get("do_not_prefer") or []),
        "shared_ok": list(SHARED_PATHS),
        "mcp_config": surf.get("mcp") or surf.get("config"),
        "briefing_line": (
            f"surface={pid} root={surf.get('root')} manifest={surf.get('manifest')} "
            f"— use this tree for skills/commands; do not prefer other platform dirs"
        ),
    }
