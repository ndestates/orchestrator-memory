#!/usr/bin/env python3
"""
Register every project skill + chain as slash commands on all AI surfaces.

Canonical skill source: ``.grok/skills/*/SKILL.md`` (including app-added skills).

Surfaces:
  - Grok:     user-invocable skills (``/skill-name``)
  - Claude:   ``.claude/commands/<name>.md``  (``/name``)
  - Copilot:  ``.github/skills/`` + ``.copilot/skills/``
  - Cursor:   ``.cursor/commands/<name>.md``  (``/name`` in chat)
  - Gemini:   catalog prompt ``.gemini/prompts/slash-commands.md``
  - ChatGPT:  catalog prompt ``.chatgpt/prompts/slash-commands.md``
  - Registry: ``chains/registry.yaml`` skill + chain entries
  - Catalog:  ``docs/reference/slash-commands.md`` + ``chains/slash-catalog.yaml``

Usage:
  python3 scripts/register-all-slash-commands.py
  python3 scripts/register-all-slash-commands.py --check   # report gaps, exit 1 if any
  python3 scripts/register-all-slash-commands.py --dry-run

Also run after adding skills under .grok/skills/ or app skill drops.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _engine.roots import default_main_root, set_template_root  # noqa: E402

ROOT = default_main_root(Path(__file__))
set_template_root(ROOT)

import yaml  # noqa: E402

from _engine import sync_grok as _sync  # noqa: E402

SKIP_SLASH = frozenset({"copilot-instructions"})
GROK_SKILLS = ROOT / ".grok" / "skills"
CLAUDE_CMDS = ROOT / ".claude" / "commands"
CURSOR_CMDS = ROOT / ".cursor" / "commands"
GEMINI_PROMPTS = ROOT / ".gemini" / "prompts"
CHATGPT_PROMPTS = ROOT / ".chatgpt" / "prompts"
CATALOG_MD = ROOT / "docs" / "reference" / "slash-commands.md"
CATALOG_YAML = ROOT / "chains" / "slash-catalog.yaml"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in fm_raw.splitlines():
        if line.startswith("  ") and key:
            buf.append(line.strip())
            continue
        if key:
            data[key] = " ".join(buf).strip().strip("'\"")
            buf = []
            key = None
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v.startswith(">"):
                key = k
                buf = []
            elif v:
                data[k] = v.strip("'\"")
            else:
                key = k
                buf = []
    if key:
        data[key] = " ".join(buf).strip().strip("'\"")
    return data, body


def iter_grok_skills() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    if not GROK_SKILLS.is_dir():
        return out
    for skill_md in sorted(GROK_SKILLS.rglob("SKILL.md")):
        rel = str(skill_md.parent.relative_to(GROK_SKILLS)).replace("\\", "/")
        if rel in SKIP_SLASH:
            continue
        out.append((rel, skill_md))
    return out


def slash_name(skill_dir: str, meta: dict[str, str]) -> str:
    mapped = _sync.claude_command_name(skill_dir)
    if mapped:
        return mapped
    name = (meta.get("name") or skill_dir).strip()
    return name.replace("/", "-").lstrip("/")


def ensure_user_invocable(skill_md: Path, dry_run: bool) -> bool:
    """Add user-invocable: true when frontmatter lacks it (do not override false)."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    fm = text[4:end]
    if re.search(r"^user-invocable:\s*", fm, re.M):
        return False
    # insert after name: or at end of frontmatter
    lines = fm.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("name:"):
            insert_at = i + 1
            break
    lines.insert(insert_at, "user-invocable: true")
    new_fm = "\n".join(lines)
    new_text = "---\n" + new_fm + "\n---\n" + text[end + 5 :]
    if not dry_run:
        skill_md.write_text(new_text, encoding="utf-8")
    return True


def skill_to_cursor_command(skill_md: Path, cmd_name: str) -> str:
    text = skill_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    desc = meta.get("description") or f"Run /{cmd_name}"
    desc = " ".join(desc.split())
    if len(desc) > 200:
        desc = desc[:197] + "..."
    hint = meta.get("argument-hint") or ""
    # Cursor commands: markdown body is the prompt when /cmd is chosen
    lines = [
        f"# /{cmd_name}",
        "",
        f"> {desc}",
        "",
        f"**Platform:** Cursor · same skill as Grok `/{cmd_name}` · Claude `/{cmd_name}`",
        "",
        "Execute this skill for the current project. Cache-first. Manifest-first.",
        "",
    ]
    if hint:
        lines.append(f"Argument hint: `{hint}`")
        lines.append("")
    lines.append(body.strip())
    lines.append("")
    lines.append("User focus (optional): use any extra chat text as $ARGUMENTS.")
    lines.append("")
    return "\n".join(lines)


def write_cursor_commands(skills: list[tuple[str, Path]], dry_run: bool) -> list[str]:
    written: list[str] = []
    if not dry_run:
        CURSOR_CMDS.mkdir(parents=True, exist_ok=True)
    for skill_dir, skill_md in skills:
        meta, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        cmd = slash_name(skill_dir, meta)
        dest = CURSOR_CMDS / f"{cmd}.md"
        content = skill_to_cursor_command(skill_md, cmd)
        if not dry_run:
            dest.write_text(content, encoding="utf-8")
        written.append(str(dest.relative_to(ROOT)))
    # Canonical chain command for Cursor
    chain_body = """# /chain

Run an orchestrator **chain** by id (same as Grok and Claude).

**Default session opener:**

```text
/chain session-start
```

Other common ids: `eod-shutdown`, `session-end`, `delivery`, `always-on-memory`, `code-review`.

1. Read `CHAIN.md` or `chains/registry.yaml` for the chain id.
2. Follow `.cursor` rules + project cache (manifest-first).
3. Execute chain steps cache-first; cite cache files used.

User focus: the chain id or intent (e.g. `session-start`).
"""
    chain_dest = CURSOR_CMDS / "chain.md"
    if not dry_run:
        chain_dest.write_text(chain_body, encoding="utf-8")
    written.append(str(chain_dest.relative_to(ROOT)))
    return written


def build_catalog(
    skills: list[tuple[str, Path]],
    chains: list[dict],
) -> tuple[str, dict]:
    skill_rows: list[dict] = []
    for skill_dir, skill_md in skills:
        meta, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        cmd = slash_name(skill_dir, meta)
        skill_rows.append(
            {
                "slash": f"/{cmd}",
                "id": cmd,
                "skill_dir": skill_dir,
                "description": " ".join(
                    (meta.get("description") or skill_dir).split()
                )[:160],
                "grok": f".grok/skills/{skill_dir}/SKILL.md",
                "claude": f".claude/commands/{cmd}.md",
                "cursor": f".cursor/commands/{cmd}.md",
                "github": f".github/skills/{skill_dir}/SKILL.md",
            }
        )
    skill_rows.sort(key=lambda r: r["slash"])

    chain_rows = []
    for c in chains:
        cid = c.get("id")
        if not cid:
            continue
        chain_rows.append(
            {
                "slash": f"/chain {cid}",
                "id": cid,
                "name": c.get("name") or cid,
                "description": " ".join(str(c.get("description") or "").split())[:160],
            }
        )
    chain_rows.sort(key=lambda r: r["id"])

    data = {
        "version": 1,
        "canonical_session": "/chain session-start",
        "skills": skill_rows,
        "chains": chain_rows,
    }

    md_lines = [
        "# Slash commands catalog",
        "",
        "[UPDATED by scripts/register-all-slash-commands.py]",
        "",
        "Every skill under `.grok/skills/` is registered for **Grok**, **Claude**, **Copilot**, and **Cursor**.",
        "",
        "## Canonical session opener",
        "",
        "```text",
        "/chain session-start",
        "```",
        "",
        "Type that on the **Grok** or **Claude** command line (chain skill / command).",
        "",
        "## Skills (slash)",
        "",
        "| Slash | Description |",
        "|-------|-------------|",
    ]
    for r in skill_rows:
        desc = r["description"].replace("|", "\\|")
        md_lines.append(f"| `{r['slash']}` | {desc} |")
    md_lines.extend(
        [
            "",
            "## Chains",
            "",
            "Invoke via **`/chain <id>`** (same on Grok · Claude · Cursor `/chain`).",
            "",
            "| Slash | Name |",
            "|-------|------|",
        ]
    )
    for r in chain_rows:
        md_lines.append(f"| `/chain {r['id']}` | {r['name']} |")
    md_lines.extend(
        [
            "",
            "## Surfaces",
            "",
            "| Host | How slashes appear |",
            "|------|-------------------|",
            "| Grok | `.grok/skills/*/SKILL.md` with `user-invocable: true` → `/name` |",
            "| Claude Code | `.claude/commands/<name>.md` → `/name` |",
            "| Cursor | `.cursor/commands/<name>.md` → `/name` in chat |",
            "| Copilot | `.github/skills/` + `.copilot/skills/` |",
            "| Gemini / ChatGPT | This catalog under `.gemini/prompts/` / `.chatgpt/prompts/` |",
            "",
            "Re-run: `python3 scripts/register-all-slash-commands.py`",
            "",
        ]
    )
    return "\n".join(md_lines), data


def write_prompt_catalog(dest: Path, title: str, md_body: str, dry_run: bool) -> str:
    # Strip the H1 and use host-specific header
    body = md_body
    if body.startswith("# "):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    content = f"# {title}\n\n{body.strip()}\n"
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    return str(dest.relative_to(ROOT))


def gap_report(skills: list[tuple[str, Path]]) -> list[str]:
    gaps: list[str] = []
    for skill_dir, skill_md in skills:
        meta, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        cmd = slash_name(skill_dir, meta)
        claude = CLAUDE_CMDS / f"{cmd}.md"
        cursor = CURSOR_CMDS / f"{cmd}.md"
        github = ROOT / ".github" / "skills" / skill_dir / "SKILL.md"
        if not claude.is_file():
            gaps.append(f"missing Claude command: /{cmd} ({skill_dir})")
        if not cursor.is_file():
            gaps.append(f"missing Cursor command: /{cmd} ({skill_dir})")
        if skill_dir not in _sync.AGENT_SKILLS and not github.is_file():
            gaps.append(f"missing GitHub skill: {skill_dir}")
    if not (CLAUDE_CMDS / "chain.md").is_file():
        gaps.append("missing Claude /chain command")
    if not (CURSOR_CMDS / "chain.md").is_file():
        gaps.append("missing Cursor /chain command")
    return gaps


def load_chains() -> list[dict]:
    reg = ROOT / "chains" / "registry.yaml"
    if not reg.is_file():
        return []
    data = yaml.safe_load(reg.read_text(encoding="utf-8")) or {}
    return list(data.get("chains") or [])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report gaps only")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-sync", action="store_true", help="skip full sync_grok")
    args = ap.parse_args()

    skills = iter_grok_skills()
    print(f"register-all-slash-commands: {len(skills)} grok skills")

    if args.check:
        gaps = gap_report(skills)
        for g in gaps:
            print(f"  GAP: {g}")
        print(f"  total gaps: {len(gaps)}")
        return 1 if gaps else 0

    # 1) Ensure Grok user-invocable
    inv_added = 0
    for _skill_dir, skill_md in skills:
        if ensure_user_invocable(skill_md, args.dry_run):
            inv_added += 1
    print(f"  user-invocable ensured: {inv_added}")

    # 2) App registry overlay (project-local skills → chains/registry)
    if not args.dry_run:
        import importlib.util

        reg_path = _SCRIPTS / "register-project-skills.py"
        spec = importlib.util.spec_from_file_location(
            "register_project_skills_mod", reg_path
        )
        if not spec or not spec.loader:
            print("  register-project-skills: cannot load", file=sys.stderr)
            return 1
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rc = int(mod.main())
        if rc != 0:
            print("  register-project-skills failed", file=sys.stderr)
            return rc

    # 3) Sync grok → github / claude / copilot
    if not args.skip_sync and not args.dry_run:
        import os

        os.environ.setdefault("ORCHESTRATOR_QUIET", "1")
        _sync.main()
        print("  sync_grok: done")

    # 4) Cursor commands for every skill
    cursor_files = write_cursor_commands(skills, args.dry_run)
    print(f"  cursor commands: {len(cursor_files)}")

    # 5) Catalogs
    chains = load_chains()
    md, data = build_catalog(skills, chains)
    if not args.dry_run:
        CATALOG_MD.parent.mkdir(parents=True, exist_ok=True)
        CATALOG_MD.write_text(md, encoding="utf-8")
        CATALOG_YAML.write_text(
            yaml.dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    print(f"  catalog: {CATALOG_MD.relative_to(ROOT)}")
    print(f"  catalog: {CATALOG_YAML.relative_to(ROOT)}")

    g = write_prompt_catalog(
        GEMINI_PROMPTS / "slash-commands.md",
        "Slash commands (Gemini) — paste or invoke by name",
        md,
        args.dry_run,
    )
    c = write_prompt_catalog(
        CHATGPT_PROMPTS / "slash-commands.md",
        "Slash commands (ChatGPT / Codex) — paste or invoke by name",
        md,
        args.dry_run,
    )
    print(f"  gemini: {g}")
    print(f"  chatgpt: {c}")

    # 6) Final gap check
    gaps = gap_report(skills) if not args.dry_run else []
    if gaps:
        print(f"  remaining gaps: {len(gaps)}")
        for g in gaps[:20]:
            print(f"    - {g}")
        if len(gaps) > 20:
            print(f"    … +{len(gaps) - 20} more")
        return 1

    print(
        f"  OK — skills={len(skills)} chains={len(chains)} "
        f"canonical=/chain session-start"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
