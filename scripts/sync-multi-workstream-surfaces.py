#!/usr/bin/env python3
"""Sync multi-workstream procedure text to every AI platform surface.

Canonical contract: docs/guides/multi-workstream/IMPLEMENTATION.md
Runtime: scripts/workstream.py + workstream_graph_example.py (unchanged).

Usage:
  python3 scripts/sync-multi-workstream-surfaces.py
  python3 scripts/sync-multi-workstream-surfaces.py --check   # exit 1 if drift
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "docs" / "guides" / "multi-workstream" / "IMPLEMENTATION.md"

# Shared body after host banner (sections 1–7 from IMPLEMENTATION, no platform map)
BODY_START = "## 1. Operator slash commands"
BODY_END = "## 8. Platform surface map"

HOSTS = [
    {
        "id": "grok",
        "path": ".grok/skills/multi-workstream/SKILL.md",
        "kind": "skill",
        "banner": (
            "**THIS SURFACE IS GROK — use `.grok/` only for skills.**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/grok.md",
        "frontmatter": """---
name: multi-workstream
description: >
  Multi-workstream session v2 + agent graphs. Operator UX is slash commands
  (/multi-workstream …). Same implementation on every host. Not multi-session SDK.
argument-hint: "[list | brief | graph | focus <id> [--apply] | hold <id> [--ready] | note <id> --next … | example | diamond]"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - bash
  - read_file
---
""",
    },
    {
        "id": "claude",
        "path": ".claude/commands/multi-workstream.md",
        "kind": "command",
        "banner": (
            "**THIS SURFACE IS CLAUDE CODE — use `.claude/` only for commands/agents.**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/claude.md",
        "frontmatter": """---
description: Multi-workstream tracks + diamond demo. Slash-first; same implementation all hosts.
argument-hint: "[list | brief | graph | focus <id> [--apply] | hold <id> [--ready] | note <id> --next … | example | diamond]"
allowed-tools: Bash, Read
---
""",
        "footer": "\n$ARGUMENTS\n",
    },
    {
        "id": "github",
        "path": ".github/skills/multi-workstream/SKILL.md",
        "kind": "skill",
        "banner": (
            "**THIS SURFACE IS GITHUB COPILOT — use `.github/skills/` (and `.copilot/skills/`).**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/copilot.md",
        "frontmatter": """---
name: multi-workstream
description: >
  Multi-workstream session v2 + agent graphs. Operator UX is slash commands
  (/multi-workstream …). Same implementation on every host. Not multi-session SDK.
argument-hint: "[list | brief | graph | focus <id> [--apply] | hold <id> [--ready] | note <id> --next … | example | diamond]"
---
""",
    },
    {
        "id": "copilot",
        "path": ".copilot/skills/multi-workstream/SKILL.md",
        "kind": "skill",
        "banner": (
            "**THIS SURFACE IS COPILOT (VS Code) — use `.copilot/skills/` / `.github/`.**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/copilot.md",
        "frontmatter": """---
name: multi-workstream
description: >
  Multi-workstream session v2 + agent graphs. Operator UX is slash commands
  (/multi-workstream …). Same implementation on every host. Not multi-session SDK.
argument-hint: "[list | brief | graph | focus <id> [--apply] | hold <id> [--ready] | note <id> --next … | example | diamond]"
---
""",
    },
    {
        "id": "chatgpt",
        "path": ".chatgpt/prompts/multi-workstream.md",
        "kind": "prompt",
        "banner": (
            "**THIS SURFACE IS CHATGPT / CODEX — use `.chatgpt/` only for prompts/instructions.**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/chatgpt.md",
        "frontmatter": "",
    },
    {
        "id": "gemini",
        "path": ".gemini/prompts/multi-workstream.md",
        "kind": "prompt",
        "banner": (
            "**THIS SURFACE IS GEMINI — use `.gemini/` only for prompts/instructions.**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/gemini.md",
        "frontmatter": "",
    },
    {
        "id": "cursor",
        "path": ".cursor/rules/multi-workstream.mdc",
        "kind": "rule",
        "banner": (
            "**THIS SURFACE IS CURSOR — use `.cursor/` only for rules/MCP.**\n"
            "Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.\n"
        ),
        "guide": "docs/guides/multi-workstream/cursor.md",
        "frontmatter": """---
description: Multi-workstream slash-first — same implementation as all hosts (/multi-workstream …)
globs:
alwaysApply: false
---
""",
    },
]

# Also mirror implementation into skill references for offline agents
REF_PATH = ".grok/skills/multi-workstream/references/IMPLEMENTATION.md"


def extract_shared_body(impl_text: str) -> str:
    start = impl_text.find(BODY_START)
    end = impl_text.find(BODY_END)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("IMPLEMENTATION.md missing section markers for body extract")
    body = impl_text[start:end].rstrip() + "\n"
    # Drop section 8 pointer noise; keep 1–7
    return body


def render_host(host: dict, body: str) -> str:
    parts = []
    fm = host.get("frontmatter") or ""
    if fm:
        parts.append(fm.rstrip() + "\n")
    parts.append("# Multi-workstream + agent graphs\n\n")
    parts.append(host["banner"] + "\n")
    parts.append(
        "**Same implementation on every AI host** (Grok · Claude · Copilot · ChatGPT · "
        "Gemini · Cursor). Only this banner’s primary tree differs.\n\n"
        "**Operator UX = slash commands.** Scripts under `scripts/` are agent/CI "
        "implementation — do **not** present `python3 scripts/…` as the primary operator interface.\n\n"
    )
    parts.append(body)
    if not body.endswith("\n"):
        parts.append("\n")
    parts.append(f"\n## This host\n\n")
    parts.append(f"- Procedure entry: `{host['path']}`\n")
    parts.append(f"- Guide: `{host['guide']}`\n")
    parts.append("- Canonical contract: `docs/guides/multi-workstream/IMPLEMENTATION.md`\n")
    parts.append("- Sync: `python3 scripts/sync-multi-workstream-surfaces.py`\n")
    footer = host.get("footer") or ""
    if footer:
        parts.append(footer)
    return "".join(parts)


def render_guide(host_id: str, title: str, surface: str, body_ops: str) -> str:
    """Per-LLM guide: same steps, surface-specific header."""
    return f"""# Multi-workstream — {title}

[UPDATED 2026-07-22]

**You are {title}.** Primary tree: **`{surface}`** only.  
**Implementation is identical on all hosts** — see [IMPLEMENTATION.md](IMPLEMENTATION.md).  
Hub: [Multi-workstream (all platforms)](../multi-workstream.md).

| Use | Path |
|-----|------|
| Procedure | see IMPLEMENTATION §8 for this host |
| Shared runtime | `scripts/workstream.py`, `scripts/workstream_graph_example.py` |
| Registry | `reports/sessions/workstreams.yaml` |
| Do not use as primary | other `.platform/` trees |

## 1. Start the day

```text
/chain session-start
```

Expect CTX including `ws primary=…`. Answer `ask:` if present.

## 2. Day-to-day (slash — same as every model)

| Goal | Type |
|------|------|
| List tracks | `/multi-workstream list` |
| Brief | `/multi-workstream brief` |
| Graph | `/multi-workstream graph` |
| Set primary | `/multi-workstream focus <id>` |
| Primary + checkout | `/multi-workstream focus <id> --apply` |
| Hold ready | `/multi-workstream hold <id> --ready` |
| Note next | `/multi-workstream note <id> --next "…"` |
| Graph example | `/multi-workstream example` |
| Pack | `/chain multi-workstream` |
| Graph chain | `/chain workstream-graph-demo` |

## 3. Typical day

```text
/chain session-start
/multi-workstream list
/multi-workstream example
/chain session-end
```

## 4. Pasteable prompt

```text
Primary surface: {surface} only. Multi-workstream implementation is shared (IMPLEMENTATION.md).
1) /chain session-start — print CTX including ws line
2) /multi-workstream list
3) Do not expand held / held_ready tracks unless I say unhold
4) On request: /multi-workstream example — summarize diamond reduce only
Never ask me to type python3 scripts/workstream.py as the main interface.
```

## 5. Agent implementation map

Identical on all hosts — [IMPLEMENTATION.md §2](IMPLEMENTATION.md).

## 6. Don’t

| Don’t | Why |
|-------|-----|
| Different commands per model | Contract is shared |
| Prefer raw python for operators | Slash-first |
| Unhold without ask | Policy |
| Multi-session SDK | Tracks ≠ N chats |

## Next

- [IMPLEMENTATION](IMPLEMENTATION.md) · [Hub](../multi-workstream.md)
"""


GUIDE_META = [
    ("grok", "Grok Build", ".grok/"),
    ("claude", "Claude Code", ".claude/"),
    ("copilot", "GitHub Copilot", ".github/ + .copilot/"),
    ("chatgpt", "ChatGPT / Codex", ".chatgpt/"),
    ("gemini", "Google Gemini", ".gemini/"),
    ("cursor", "Cursor", ".cursor/"),
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if surfaces drift")
    args = ap.parse_args(argv)

    if not IMPL.is_file():
        print(f"missing {IMPL}", file=sys.stderr)
        return 1
    impl = IMPL.read_text(encoding="utf-8")
    body = extract_shared_body(impl)

    drift = []
    written = []

    # Reference copy for Grok skill
    ref = ROOT / REF_PATH
    ref_content = impl
    if args.check:
        if not ref.is_file() or ref.read_text(encoding="utf-8") != ref_content:
            drift.append(str(ref.relative_to(ROOT)))
    else:
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(ref_content, encoding="utf-8")
        written.append(str(ref.relative_to(ROOT)))

    for host in HOSTS:
        path = ROOT / host["path"]
        content = render_host(host, body)
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                drift.append(host["path"])
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written.append(host["path"])

    for gid, title, surface in GUIDE_META:
        gpath = ROOT / "docs" / "guides" / "multi-workstream" / f"{gid}.md"
        gcontent = render_guide(gid, title, surface, body)
        if args.check:
            if not gpath.is_file() or gpath.read_text(encoding="utf-8") != gcontent:
                drift.append(str(gpath.relative_to(ROOT)))
        else:
            gpath.write_text(gcontent, encoding="utf-8")
            written.append(str(gpath.relative_to(ROOT)))

    # github prompt thin pointer (same impl, points to skill)
    prompt_path = ROOT / ".github" / "prompts" / "multi-workstream.prompt.md"
    prompt = """---
description: Multi-workstream (slash-first; same implementation all hosts)
---

# Multi-workstream

Use skill `.github/skills/multi-workstream/SKILL.md` (identical contract to Grok/Claude/…).

Operator: `/multi-workstream list|brief|graph|focus|hold|example`  
Chains: `/chain multi-workstream` · `/chain workstream-graph-demo` · `/chain multi-workstream-demo`  
Canonical: `docs/guides/multi-workstream/IMPLEMENTATION.md`
"""
    if args.check:
        if not prompt_path.is_file() or prompt_path.read_text(encoding="utf-8") != prompt:
            drift.append(str(prompt_path.relative_to(ROOT)))
    else:
        prompt_path.write_text(prompt, encoding="utf-8")
        written.append(str(prompt_path.relative_to(ROOT)))

    if args.check:
        if drift:
            print("DRIFT:", ", ".join(drift), file=sys.stderr)
            print("Run: python3 scripts/sync-multi-workstream-surfaces.py", file=sys.stderr)
            return 1
        print("OK: multi-workstream surfaces match IMPLEMENTATION.md")
        return 0

    print(f"synced {len(written)} files from {IMPL.relative_to(ROOT)}")
    for w in written:
        print(f"  {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
