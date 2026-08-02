#!/usr/bin/env python3
"""Regenerate internal skill/chain catalogs. INTERNAL ONLY — not for release packaging."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GEN = OUT / "_generated"


def parse_skills() -> list[dict]:
    skills_dir = ROOT / ".grok" / "skills"
    skills: list[dict] = []
    for skill_md in sorted(skills_dir.glob("**/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        name = skill_md.parent.name
        desc = ""
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                m = re.search(r"^name:\s*[\"']?([^\"'\n]+)", fm, re.M)
                if m:
                    name = m.group(1).strip()
                m = re.search(
                    r"^description:\s*>?\s*\n((?:[ \t]+.+\n)+)|^description:\s*[\"'](.+?)[\"']",
                    fm,
                    re.M,
                )
                if m:
                    desc = (m.group(1) or m.group(2) or "").strip()
                    desc = re.sub(r"\s+", " ", desc)
                if not desc:
                    m = re.search(r"^description:\s*(.+)$", fm, re.M)
                    if m and not m.group(1).startswith(">"):
                        desc = m.group(1).strip().strip("\"'")
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        h1 = re.search(r"^#\s+(.+)$", body, re.M)
        title = h1.group(1).strip() if h1 else name
        invokes = set(re.findall(r"`(/[a-z0-9][a-z0-9_./-]*)`", text, re.I))
        skills.append(
            {
                "dir": str(skill_md.parent.relative_to(ROOT)),
                "name": name,
                "title": title,
                "description": desc[:400],
                "invokes": sorted(invokes)[:12],
            }
        )
    return skills


def parse_chains() -> tuple[list[dict], list[dict]]:
    reg = yaml.safe_load((ROOT / "chains" / "registry.yaml").read_text(encoding="utf-8"))
    reg_skills = [
        s for s in (reg.get("skills") or []) if isinstance(s, dict) and s.get("id")
    ]
    chains: list[dict] = []
    for c in reg.get("chains") or []:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        steps = []
        for st in c.get("steps") or []:
            if not isinstance(st, dict):
                continue
            steps.append(
                {
                    "id": st.get("id"),
                    "type": st.get("type"),
                    "invoke": st.get("invoke"),
                    "required": st.get("required"),
                    "when": st.get("when"),
                }
            )
        chains.append(
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "description": (c.get("description") or "")
                .strip()
                .replace("\n", " ")[:300],
                "intents": c.get("intents") or [],
                "token_tier": c.get("token_tier"),
                "max_steps": c.get("max_steps"),
                "max_cache_files": c.get("max_cache_files"),
                "steps": steps,
            }
        )
    return chains, reg_skills


def write_skill_md(skills: list[dict], reg_skills: list[dict]) -> None:
    reg_by_id = {s["id"]: s for s in reg_skills}
    lines = [
        "# Skills catalog (internal)\n",
        "\n> **INTERNAL — not for public release.** Generated inventory of `.grok/skills/` "
        "with why/when and invocation.\n",
        f"\n**Count:** {len(skills)} skill packages under `.grok/skills/`.\n",
        "\n## How skills are invoked\n",
        "\n| Path | How |\n|------|-----|\n",
        "| Slash / skill name | Grok: `/skill-name` or skill menu |\n",
        "| Claude | `.claude/commands/<name>.md` (synced) |\n",
        "| Copilot | `.github/skills/` or `.github/prompts/` |\n",
        "| Chain step | `chains/registry.yaml` → `steps[].invoke` |\n",
        "| Orchestrator agent | Multi-lane plan delegates to skill/agent |\n",
        "| Session-start | Envelope + thin host entrypoints |\n",
        "\n**Platform rule:** Grok uses `.grok/`, Claude `.claude/`, Copilot `.github/`, "
        "etc. Shared code lives in `scripts/`.\n",
        "\n## Catalog\n",
    ]
    for s in skills:
        inv = ", ".join(f"`{i}`" for i in s.get("invokes") or []) or "_(see SKILL.md)_"
        reg = reg_by_id.get(s["name"]) or reg_by_id.get(s["dir"].split("/")[-1])
        if reg and reg.get("slash"):
            inv = f"`{reg['slash']}`" + (
                f"; {inv}" if inv and inv != "_(see SKILL.md)_" else ""
            )
        desc = s.get("description") or s.get("title") or ""
        lines.append(f"\n### `{s['name']}`\n")
        lines.append(f"\n- **Path:** `{s['dir']}/SKILL.md`\n")
        lines.append(f"- **Title:** {s.get('title') or s['name']}\n")
        lines.append(f"- **What / why:** {desc or '_See skill body._'}\n")
        lines.append(f"- **Invocation:** {inv}\n")
        if reg:
            lines.append(f"- **Registry tier:** {reg.get('tier', '—')}\n")
            if reg.get("path"):
                lines.append(f"- **Registry path:** `{reg['path']}`\n")
    (OUT / "SKILLS-CATALOG.md").write_text("".join(lines), encoding="utf-8")


def write_chain_md(chains: list[dict]) -> None:
    clines = [
        "# Chains catalog (internal)\n",
        "\n> **INTERNAL — not for public release.** Full chain → step → skill/prompt "
        "invocation map.\n",
        f"\n**Count:** {len(chains)} chains in `chains/registry.yaml`.\n",
        "\n## How chains run\n",
        "\n1. User: `/chain <id>` or intent match (e.g. “session start”).\n",
        "2. Agent loads chain skill (`.grok/skills/chain/`) + chain block from registry "
        "(MCP `get_chain_detail` preferred).\n",
        "3. Phase 0: manifest + cache spine (`token_policy`).\n",
        "4. Steps run in order; `required: true` must succeed; `when:` may skip optional steps.\n",
        "5. Handoffs ≤80 tokens; completion via `chain-completion-write.sh`.\n",
        "\n## Catalog\n",
    ]
    for c in chains:
        clines.append(f"\n### `{c['id']}` — {c.get('name') or c['id']}\n")
        if c.get("description"):
            clines.append(f"\n{c['description']}\n")
        intents = c.get("intents") or []
        if intents:
            clines.append(
                "\n**Intents:** " + ", ".join(f"`{i}`" for i in intents[:12]) + "\n"
            )
        meta = []
        if c.get("token_tier"):
            meta.append(f"token_tier=`{c['token_tier']}`")
        if c.get("max_steps") is not None:
            meta.append(f"max_steps=`{c['max_steps']}`")
        if c.get("max_cache_files") is not None:
            meta.append(f"max_cache_files=`{c['max_cache_files']}`")
        if meta:
            clines.append("\n" + " · ".join(meta) + "\n")
        clines.append("\n| Step | Type | Invoke | Required | When |\n")
        clines.append("|------|------|--------|----------|------|\n")
        for st in c.get("steps") or []:
            clines.append(
                f"| `{st.get('id') or '—'}` | {st.get('type') or '—'} | "
                f"`{st.get('invoke') or '—'}` | {st.get('required')} | "
                f"{st.get('when') or '—'} |\n"
            )
    (OUT / "CHAINS-CATALOG.md").write_text("".join(clines), encoding="utf-8")


def main() -> int:
    GEN.mkdir(parents=True, exist_ok=True)
    skills = parse_skills()
    chains, reg_skills = parse_chains()
    (GEN / "skills.json").write_text(json.dumps(skills, indent=2) + "\n", encoding="utf-8")
    (GEN / "chains.json").write_text(json.dumps(chains, indent=2) + "\n", encoding="utf-8")
    (GEN / "registry-skills.json").write_text(
        json.dumps(reg_skills, indent=2) + "\n", encoding="utf-8"
    )
    write_skill_md(skills, reg_skills)
    write_chain_md(chains)
    print(f"skills={len(skills)} chains={len(chains)} → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
