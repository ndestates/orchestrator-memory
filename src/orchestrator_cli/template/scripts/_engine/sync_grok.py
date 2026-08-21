"""Sync .grok/ to .github/, .claude/, .copilot/ (engine module)."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from _engine.roots import lazy_root

ROOT = lazy_root()
GROK = ROOT / ".grok"
GITHUB = ROOT / ".github"
CLAUDE = ROOT / ".claude"
COPILOT = ROOT / ".copilot"

# Thin agent-wrapper skills: sync agent file, not a duplicate skill body.
AGENT_SKILLS = {
    "bug-hunter-agent",
    "cyber-security-essentials",
    "branch-context-agent",
    "github-expert",
    "github-workflow-expert",
    "laravel-expert-agent",
    "loop-verifier",
    "mysql-database-expert",
    "mariadb-database-expert",
    "sqlite-database-expert",
    "readme-specialist",
    "schema-audit-agent",
    "security-audit-agent",
    "test-safety-agent",
    "todo-specialist-agent",
    "documentation-specialist",
    "orchestrator-deploy",
}

# Skills with full bodies in .github/skills/ (git-workflow already complete there).
GITHUB_SKILL_SKIP_IF_FULLER = {"git-workflow-guardrails"}

# grok agent filename -> (.github agents filename, .claude agent short name)
AGENT_MAP = {
    "bug-hunter-agent.md": ("bug-hunter-agent.agent.md", "bug-hunter"),
    "cyber-security-essentials.md": ("cyber-security-essentials.agent.md", "cyber-security-essentials"),
    "branch-context-agent.md": ("branch-context-agent.agent.md", "branch-context"),
    "github-expert.md": ("github-expert.agent.md", "github-expert"),
    "github-workflow-expert.md": ("github-workflow-expert.agent.md", "github-workflow-expert"),
    "laravel-expert-agent.md": ("laravel-expert-agent.md", "laravel-expert"),
    "mysql-database-expert.md": ("mysql-database-expert.agent.md", "mysql-database-expert"),
    "mariadb-database-expert.md": ("mariadb-database-expert.agent.md", "mariadb-database-expert"),
    "sqlite-database-expert.md": ("sqlite-database-expert.agent.md", "sqlite-database-expert"),
    "data-architect-expert.md": ("data-architect-expert.agent.md", "data-architect-expert"),
    "vector-database-expert.md": ("vector-database-expert.agent.md", "vector-database-expert"),
    "nextjs-expert.md": ("nextjs-expert.agent.md", "nextjs-expert"),
    "astro-expert.md": ("astro-expert.agent.md", "astro-expert"),
    "nuxt-expert.md": ("nuxt-expert.agent.md", "nuxt-expert"),
    "go-expert.md": ("go-expert.agent.md", "go-expert"),
    "docker-expert.md": ("docker-expert.agent.md", "docker-expert"),
    "readme-specialist.md": ("readme-specialist.md", "readme-specialist"),
    "schema-audit-agent.md": ("schema-audit-agent.agent.md", "schema-audit"),
    "security-audit-agent.md": ("security-audit-agent.agent.md", "security-audit"),
    "test-safety-agent.md": ("test-safety-agent.agent.md", "test-safety"),
    "test-specialist-agent.md": ("test-specialist-agent.md", "test-specialist"),
    "todo-specialist-agent.md": ("todo-specialist-agent.md", "todo-specialist"),
    "loop-verifier.md": ("loop-verifier.agent.md", "loop-verifier"),
    "documentation-specialist.md": ("documentation-specialist.md", "documentation-specialist"),
    "orchestrator-deploy.md": ("orchestrator-deploy.md", "orchestrator-deploy"),
    "find-skills.md": ("find-skills.agent.md", "find-skills"),
    "grill-me.md": ("grill-me.agent.md", "grill-me"),
    "teach.md": ("teach.agent.md", "teach"),
    "systematic-debugging.md": ("systematic-debugging.agent.md", "systematic-debugging"),
    "verification-before-completion.md": (
        "verification-before-completion.agent.md",
        "verification-before-completion",
    ),
    "code-review.md": ("code-review.agent.md", "code-review"),
    "skill-health.md": ("skill-health.agent.md", "skill-health"),
}

# grok prompt basename -> (.github prompt name, .claude command name)
PROMPT_MAP = {
    "load-project-cache-first.md": ("load-project-cache-first.prompt.md", "load-cache"),
    "daily-standup-with-cache.md": ("daily-standup-with-cache.prompt.md", "daily-standup"),
    "read-codebase.md": ("read-codebase.prompt.md", "read-codebase"),
    "model-schema-check.md": ("model-schema-check.prompt.md", "model-schema-check"),
    "filament-panel-review.md": ("filament-panel-review.prompt.md", "filament-panel-review"),
    "amazon-ses-setup.md": ("amazon-ses-setup.prompt.md", "amazon-ses-setup"),
    "aws-route53-dns-setup.md": ("aws-route53-dns-setup.prompt.md", "aws-route53-dns-setup"),
    "paypal-integration.md": ("paypal-integration.prompt.md", "paypal-integration"),
}

# grok skill dir name -> .claude command name (for user-invocable skills without separate prompts)
SKILL_COMMAND_MAP = {
    "cache-efficient": "cache-efficient",
    "token-usage-meter": "token-usage-meter",
    "ai-engineering-maturity": "ai-engineering-maturity",
    "amazon-ses-email": "amazon-ses-email",
    "aws-route53-dns": "aws-route53-dns",
    "paypal-billing-integration": "paypal-billing",
    "web-build-design": "web-build-design",
    "project-drift-guardian": "project-drift-guardian",
    "digitalocean-app-platform-docr-deploy": "digitalocean-deploy",
    "prod-db-maintenance": "prod-db-maintenance",
    "eval/maintenance-task": "eval-maintenance-task",
    "git-workflow-guardrails": "git-workflow-guardrails",
    "ddev-local-runtime": "ddev-local-runtime",
    "bug-hunter-agent": "bug-hunter",
    "cyber-security-essentials": "cyber-security-essentials",
    "security-audit-agent": "security-audit",
    "schema-audit-agent": "schema-audit",
    "test-safety-agent": "test-safety",
    "test-specialist-agent": "test-specialist",
    "todo-specialist-agent": "todo-specialist",
    "branch-context-agent": "branch-context",
    "laravel-expert-agent": "laravel-expert",
    "mysql-database-expert": "mysql-database-expert",
    "mariadb-database-expert": "mariadb-database-expert",
    "sqlite-database-expert": "sqlite-database-expert",
    "data-architect-expert": "data-architect-expert",
    "vector-database-expert": "vector-database-expert",
    "nextjs-expert": "nextjs-expert",
    "astro-expert": "astro-expert",
    "nuxt-expert": "nuxt-expert",
    "go-expert": "go-expert",
    "docker-expert": "docker-expert",
    "github-expert": "github-expert",
    "github-workflow-expert": "github-workflow-expert",
    "readme-specialist": "readme-specialist",
    "loop-triage": "loop-triage",
    "loop-verifier": "loop-verifier",
    "loop-engineering": "loop-engineering",
    "chain": "chain",
    "ddev-cleanup": "ddev-cleanup",
    "script-not-shell": "script-not-shell",
    "documentation-specialist": "documentation-specialist",
    "orchestrator-deploy": "orchestrator-deploy",
    "template-decontaminate": "template-decontaminate",
    "acquire-codebase-knowledge": "acquire-codebase-knowledge",
    "research-deep-dive": "research-deep-dive",
    "session-resume": "session-resume",
    "ai-content-guardrails": "ai-content-guardrails",
    "multi-workstream": "multi-workstream",
    "web-cache-expert": "web-cache-expert",
    "webmcp-beta": "webmcp-beta",
    "skill-health": "skill-health",
    "teach": "teach",
    "skill-creator": "skill-creator",
    "loop-compound": "loop-compound",
    "cache-freshness-check": "cache-freshness-check",
    "code-review": "code-review",
    "jersey-data-protection-expert": "jersey-data-protection-expert",
    "jersey-aml-compliance-expert": "jersey-aml-compliance-expert",
    "didit-identity-integration": "didit-identity-integration",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def strip_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 5 :]


def parse_yaml_frontmatter(fm: str) -> dict[str, str]:
    data: dict[str, str] = {}
    key = None
    buf: list[str] = []
    for line in fm.splitlines():
        if line.startswith("  ") and key:
            buf.append(line.strip())
            continue
        if key:
            data[key] = "\n".join(buf).strip().strip("'\"")
            buf = []
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith(">"):
                buf = []
            elif val.startswith('"') and val.endswith('"') and len(val) >= 2:
                data[key] = val[1:-1]
                key = None
            elif val.startswith("'") and val.endswith("'") and len(val) >= 2:
                data[key] = val[1:-1]
                key = None
            elif val:
                data[key] = val.strip("'\"")
                key = None
            else:
                buf = []
        else:
            key = None
    if key:
        data[key] = "\n".join(buf).strip().strip("'\"")
    return data


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def skill_ref(name: str) -> str:
    return f".github/skills/{name}/SKILL.md"


def prompt_ref(name: str) -> str:
    return f".github/prompts/{name}.prompt.md"


def adapt_for_github(text: str) -> str:
    slash_map = {
        "/load-project-cache-first": prompt_ref("load-project-cache-first"),
        "/daily-standup-with-cache": prompt_ref("daily-standup-with-cache"),
        "/cache-efficient": skill_ref("cache-efficient"),
        "/read-codebase": prompt_ref("read-codebase"),
        "/acquire-codebase-knowledge": skill_ref("acquire-codebase-knowledge"),
        "/model-schema-check": prompt_ref("model-schema-check"),
        "/filament-panel-review": prompt_ref("filament-panel-review"),
        "/orchestrator": "`.github/prompts/orchestrator-v2.prompt.md`",
        "/eval-maintenance-task": skill_ref("eval/maintenance-task"),
        "/project-drift-guardian": skill_ref("project-drift-guardian"),
        "/amazon-ses-email": skill_ref("amazon-ses-email"),
        "/aws-route53-dns": skill_ref("aws-route53-dns"),
        "/paypal-billing-integration": skill_ref("paypal-billing-integration"),
        "/ai-engineering-maturity": skill_ref("ai-engineering-maturity"),
        "/digitalocean-app-platform-docr-deploy": skill_ref(
            "digitalocean-app-platform-docr-deploy"
        ),
        "/git-workflow-guardrails": skill_ref("git-workflow-guardrails"),
        "/github-workflow-expert": skill_ref("github-workflow-expert"),
        "/ddev-local-runtime": skill_ref("ddev-local-runtime"),
        "/chain": skill_ref("chain"),
        "/loop-triage": skill_ref("loop-triage"),
        "/loop-verifier": skill_ref("loop-verifier"),
        "/loop-engineering": skill_ref("loop-engineering"),
        "/ddev-cleanup": skill_ref("ddev-cleanup"),
        "/script-not-shell": skill_ref("script-not-shell"),
        "/documentation-specialist": skill_ref("documentation-specialist"),
        "/orchestrator-deploy": skill_ref("orchestrator-deploy"),
    }

    replacements = [
        (".grok/skills/", ".github/skills/"),
        (".grok/agents/", ".github/agents/"),
        (".grok/prompts/", ".github/prompts/"),
        (".grok/memories/", ".copilot/memories/"),
        ("Grok-native", "Copilot-compatible"),
        ("Grok primary", "GitHub Copilot compatible"),
        ("for Grok sessions", "for Copilot sessions"),
        (".grok/ structure", ".github/ + .grok/ structure"),
        ("shared .grok/ skills/prompts/agents", "shared .github/ skills/prompts/agents"),
        ("shared .grok/ context", "shared .github/ context"),
    ]
    out = text
    for old, new in replacements:
        out = out.replace(old, new)
    for old, new in slash_map.items():
        out = out.replace(old, new)
    out = re.sub(r" skill skill", " skill", out)
    return out


def adapt_for_claude(text: str) -> str:
    slash_map = {
        "/load-project-cache-first": "/load-cache",
        "/daily-standup-with-cache": "/daily-standup",
        "/cache-efficient": "/cache-efficient",
        "/read-codebase": "/read-codebase",
        "/acquire-codebase-knowledge": "/acquire-codebase-knowledge",
        "/model-schema-check": "/model-schema-check",
        "/filament-panel-review": "/filament-panel-review",
        "/orchestrator": "/orchestrator",
        "/eval-maintenance-task": "/eval-maintenance-task",
        "/project-drift-guardian": "/project-drift-guardian",
        "/amazon-ses-email": "/amazon-ses-email",
        "/aws-route53-dns": "/aws-route53-dns",
        "/paypal-billing-integration": "/paypal-billing",
        "/ai-engineering-maturity": "/ai-engineering-maturity",
        "/digitalocean-app-platform-docr-deploy": "/digitalocean-deploy",
        "/git-workflow-guardrails": "/git-workflow-guardrails",
        "/github-workflow-expert": "/github-workflow-expert",
        "/ddev-local-runtime": "/ddev-local-runtime",
        "/chain": "/chain",
        "/loop-triage": "/loop-triage",
        "/loop-verifier": "/loop-verifier",
        "/loop-engineering": "/loop-engineering",
        "/ddev-cleanup": "/ddev-cleanup",
        "/script-not-shell": "/script-not-shell",
        "/documentation-specialist": "/documentation-specialist",
        "/orchestrator-deploy": "/orchestrator-deploy",
        "/laravel-expert-agent": "/laravel-expert",
        "/security-audit-agent": "/security-audit",
        "/schema-audit-agent": "/schema-audit",
        "/test-safety-agent": "/test-safety",
        "/test-specialist-agent": "/test-specialist",
        "/todo-specialist-agent": "/todo-specialist",
        "/branch-context-agent": "/branch-context",
        "/github-expert-agent": "/github-expert",
        "/mysql-database-expert": "/mysql-database-expert",
        "/mariadb-database-expert": "/mariadb-database-expert",
        "/sqlite-database-expert": "/sqlite-database-expert",
        "/data-architect-expert": "/data-architect-expert",
        "/vector-database-expert": "/vector-database-expert",
        "/nextjs-expert": "/nextjs-expert",
        "/astro-expert": "/astro-expert",
        "/nuxt-expert": "/nuxt-expert",
        "/go-expert": "/go-expert",
        "/docker-expert": "/docker-expert",
        "/readme-specialist": "/readme-specialist",
    }

    agent_paths = {
        "branch-context-agent.md": "branch-context.md",
        "github-expert.md": "github-expert.md",
        "laravel-expert-agent.md": "laravel-expert.md",
        "mysql-database-expert.md": "mysql-database-expert.md",
        "mariadb-database-expert.md": "mariadb-database-expert.md",
        "sqlite-database-expert.md": "sqlite-database-expert.md",
        "data-architect-expert.md": "data-architect-expert.md",
        "vector-database-expert.md": "vector-database-expert.md",
        "nextjs-expert.md": "nextjs-expert.md",
        "astro-expert.md": "astro-expert.md",
        "nuxt-expert.md": "nuxt-expert.md",
        "go-expert.md": "go-expert.md",
        "docker-expert.md": "docker-expert.md",
        "readme-specialist.md": "readme-specialist.md",
        "schema-audit-agent.md": "schema-audit.md",
        "security-audit-agent.md": "security-audit.md",
        "test-safety-agent.md": "test-safety.md",
        "test-specialist-agent.md": "test-specialist.md",
        "todo-specialist-agent.md": "todo-specialist.md",
    }

    replacements = [
        (".grok/skills/", ".claude/commands/"),
        (".grok/agents/", ".claude/agents/"),
        (".grok/prompts/", ".claude/commands/"),
        (".grok/memories/", ".copilot/memories/"),
        (".github/project-manifest.yaml", ".claude/project-manifest.yaml"),
        (".github/copilot-instructions.md", "CLAUDE.md"),
        ("[`.copilot/memories/INDEX.md`](../../memories/INDEX.md)", "`.copilot/memories/INDEX.md`"),
        (
            "[`.copilot/memories/`](../../../.copilot/memories/)",
            "`.copilot/memories/`",
        ),
    ]
    for src, dest in agent_paths.items():
        replacements.append((f".claude/agents/{src}", f".claude/agents/{dest}"))
    out = text
    for old, new in replacements:
        out = out.replace(old, new)
    for old, new in slash_map.items():
        out = out.replace(old, new)
    return out


def prompt_to_github(content: str) -> str:
    fm, body = strip_frontmatter(content)
    body = adapt_for_github(body)
    # GitHub prompts use markdown without Copilot chat frontmatter.
    return body.strip() + "\n"


def prompt_to_claude_command(content: str, command_name: str) -> str:
    fm, body = strip_frontmatter(content)
    meta = parse_yaml_frontmatter(fm) if fm else {}
    description = adapt_for_claude(
        collapse_whitespace(meta.get("description", f"Invoke {command_name}"))
    )
    argument_hint = adapt_for_claude(meta.get("argument-hint", ""))
    body = adapt_for_claude(body)
    lines = [
        "---",
        f"description: {description}",
    ]
    if argument_hint:
        lines.append(f"argument-hint: {argument_hint}")
    lines.extend(
        [
            "allowed-tools: Read, Grep, Glob, Bash",
            "---",
            "",
            body.strip(),
            "",
        ]
    )
    if argument_hint:
        lines.append(f"User focus (optional): $ARGUMENTS")
        lines.append("")
    return "\n".join(lines)


def write_copilot_skill(skill_name: str, content: str, created: list[str]) -> None:
    """Mirror a skill body to .copilot/skills/ (Copilot parity with .github/skills/)."""
    dest = COPILOT / "skills" / skill_name / "SKILL.md"
    write_text(dest, content)
    created.append(str(dest.relative_to(ROOT)))


def skill_to_github(skill_path: Path, skill_name: str) -> str:
    content = read_text(skill_path)
    if skill_name in GITHUB_SKILL_SKIP_IF_FULLER:
        existing = GITHUB / "skills" / skill_name / "SKILL.md"
        if existing.exists() and len(read_text(existing)) > len(content):
            return read_text(existing)
    return adapt_for_github(content)


def skill_to_claude_command(skill_path: Path, command_name: str) -> str:
    content = read_text(skill_path)
    fm, body = strip_frontmatter(content)
    meta = parse_yaml_frontmatter(fm) if fm else {}
    description = adapt_for_claude(
        collapse_whitespace(meta.get("description", f"Invoke {command_name}"))
    )
    argument_hint = adapt_for_claude(meta.get("argument-hint", ""))
    body = adapt_for_claude(body)
    lines = [
        "---",
        f"description: {description}",
    ]
    if argument_hint:
        lines.append(f"argument-hint: {argument_hint}")
    lines.extend(
        [
            "allowed-tools: Read, Grep, Glob, Bash",
            "---",
            "",
            body.strip(),
            "",
        ]
    )
    if argument_hint:
        lines.append(f"User focus (optional): $ARGUMENTS")
        lines.append("")
    return "\n".join(lines)


def agent_to_github(agent_path: Path, skill_path: Path | None) -> str:
    content = read_text(agent_path)
    fm, body = strip_frontmatter(content)
    meta = parse_yaml_frontmatter(fm) if fm else {}
    name = meta.get("name", agent_path.stem)
    description = meta.get("description", "")

    skill_notes = ""
    if skill_path and skill_path.exists():
        sfm, sbody = strip_frontmatter(read_text(skill_path))
        skill_notes = adapt_for_github(sbody.strip())

    header = f"# {name}\n\n"
    if description:
        header += f"## Role\n{description}\n\n"
    header += "## Source\nSynced from `.grok/agents/` for Copilot parity.\n\n"

    merged = header + adapt_for_github(body.strip())
    if skill_notes and len(skill_notes) > 80:
        merged += "\n\n## Execution Notes (from skill)\n\n" + skill_notes
    return merged + "\n"


def agent_to_claude(agent_path: Path, short_name: str, skill_path: Path | None) -> str:
    content = read_text(agent_path)
    fm, body = strip_frontmatter(content)
    meta = parse_yaml_frontmatter(fm) if fm else {}
    description = collapse_whitespace(
        meta.get("description", f"Specialist agent for {short_name.replace('-', ' ')}.")
    )

    read_only = short_name in {"schema-audit", "security-audit", "test-safety", "branch-context"}
    tools = "Read, Grep, Glob, Bash" if read_only else "Read, Edit, Write, Grep, Glob, Bash"

    skill_notes = ""
    if skill_path and skill_path.exists():
        _, sbody = strip_frontmatter(read_text(skill_path))
        skill_notes = adapt_for_claude(sbody.strip())

    body = adapt_for_claude(body.strip())
    lines = [
        "---",
        f"name: {short_name}",
        f"description: {description}",
        f"tools: {tools}",
        "---",
        "",
        body,
    ]
    if skill_notes and len(skill_notes) > 80:
        lines.extend(["", "## Execution Notes", "", skill_notes])
    lines.append("")
    return "\n".join(lines)


def build_ddev_skill() -> str:
    copilot = read_text(GROK / "skills" / "copilot-instructions" / "SKILL.md")
    _, body = strip_frontmatter(copilot)
    section = re.search(
        r"(## 2\) DDEV Runtime Rules.*?)(?=\n## 3\))",
        body,
        re.DOTALL,
    )
    ddev_body = section.group(1).strip() if section else body
    grok_notes = read_text(GROK / "skills" / "ddev-local-runtime" / "SKILL.md")
    _, gn = strip_frontmatter(grok_notes)
    return f"""---
name: ddev-local-runtime
description: 'Mandatory rule that all local project commands for the project repository run inside the DDEV runtime, not on the host shell. Apply when about to run php, composer, artisan, npm, node, python3, pip, mysql, pest, phpunit, or any project tooling locally.'
user-invocable: true
disable-model-invocation: false
---

# DDEV is the local runtime — host shell is not supported

{adapt_for_github(ddev_body)}

## Copilot execution notes

{adapt_for_github(gn.strip())}
"""


def build_copilot_instructions() -> str:
    content = read_text(GROK / "skills" / "copilot-instructions" / "SKILL.md")
    _, body = strip_frontmatter(content)
    body = adapt_for_github(body)
    body = body.replace(
        "**This is the primary version for Grok.**",
        "**This file is maintained for GitHub Copilot and GitHub-native tools.**",
    )
    body = body.replace(
        "Grok sessions should prefer this `.grok/skills/copilot-instructions/SKILL.md`.",
        "Grok sessions use the parallel `.grok/skills/copilot-instructions/SKILL.md`.",
    )
    body = re.sub(r"## Grok-specific Notes\n.*?(?=\n## |\Z)", "", body, flags=re.DOTALL)
    header = """# Project AI Agent Instructions

This guide defines practical, security-first operating rules for AI-assisted development in this repository.

"""
    return header + body.strip() + "\n"


# Meta / non-slash skills (never become Claude/Cursor slash commands)
SKIP_SLASH_SKILLS = frozenset({"copilot-instructions"})


def sync_skill_assets(skill_root: Path, skill_name: str, created: list[str]) -> None:
    """Copy scripts/, references/, assets/ to GitHub and Copilot skill trees."""
    for sub in ("scripts", "references", "assets"):
        src_sub = skill_root / sub
        if not src_sub.is_dir():
            continue
        for path in src_sub.rglob("*"):
            if path.is_dir() or path.name == "__pycache__":
                continue
            rel_asset = path.relative_to(skill_root)
            for base in (GITHUB / "skills" / skill_name, COPILOT / "skills" / skill_name):
                dest_asset = base / rel_asset
                dest_asset.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest_asset)
                created.append(str(dest_asset.relative_to(ROOT)))


def claude_command_name(skill_name: str) -> str | None:
    """Map .grok skill dir → Claude / Cursor slash command name.

    SKILL_COMMAND_MAP holds renames (e.g. laravel-expert-agent → laravel-expert).
    Every other skill defaults to its directory name (slashes → hyphens).
    """
    if skill_name in SKIP_SLASH_SKILLS:
        return None
    if skill_name in SKILL_COMMAND_MAP:
        return SKILL_COMMAND_MAP[skill_name]
    return skill_name.replace("/", "-")


def sync_skills() -> list[str]:
    created: list[str] = []
    for skill_dir in sorted((GROK / "skills").rglob("SKILL.md")):
        rel = skill_dir.relative_to(GROK / "skills")
        skill_name = str(rel.parent)
        if skill_name == "copilot-instructions":
            continue
        if skill_name in AGENT_SKILLS:
            # Agent-wrapper skills: github/copilot body + Claude command come from
            # sync_agents (and ensure_claude_command below for any missed).
            cmd_name = claude_command_name(skill_name)
            if cmd_name:
                cmd_dest = CLAUDE / "commands" / f"{cmd_name}.md"
                write_text(cmd_dest, skill_to_claude_command(skill_dir, cmd_name))
                created.append(str(cmd_dest.relative_to(ROOT)))
            sync_skill_assets(skill_dir.parent, skill_name, created)
            continue

        dest = GITHUB / "skills" / skill_name / "SKILL.md"
        if skill_name == "ddev-local-runtime":
            content = build_ddev_skill()
        else:
            content = skill_to_github(skill_dir, skill_name)
        write_text(dest, content)
        created.append(str(dest.relative_to(ROOT)))
        write_copilot_skill(skill_name, content, created)

        sync_skill_assets(skill_dir.parent, skill_name, created)

        # ALL skills get a Claude slash command (not only SKILL_COMMAND_MAP)
        cmd_name = claude_command_name(skill_name)
        if cmd_name:
            cmd_dest = CLAUDE / "commands" / f"{cmd_name}.md"
            if skill_name == "ddev-local-runtime":
                cmd_content = skill_to_claude_command(
                    GROK / "skills" / "ddev-local-runtime" / "SKILL.md", cmd_name
                )
                cmd_content = cmd_content.replace(
                    "The full DDEV local runtime rules",
                    "See also CLAUDE.md §2. Full DDEV local runtime rules",
                )
            else:
                cmd_content = skill_to_claude_command(skill_dir, cmd_name)
            write_text(cmd_dest, cmd_content)
            created.append(str(cmd_dest.relative_to(ROOT)))
    return created


def sync_prompts() -> list[str]:
    created: list[str] = []
    for prompt_file in sorted((GROK / "prompts").glob("*.md")):
        gh_name, cl_name = PROMPT_MAP.get(
            prompt_file.name, (prompt_file.stem + ".prompt.md", prompt_file.stem)
        )
        content = read_text(prompt_file)
        write_text(GITHUB / "prompts" / gh_name, prompt_to_github(content))
        write_text(
            CLAUDE / "commands" / f"{cl_name}.md",
            prompt_to_claude_command(content, cl_name),
        )
        created.append(str((GITHUB / "prompts" / gh_name).relative_to(ROOT)))
        created.append(str((CLAUDE / "commands" / f"{cl_name}.md").relative_to(ROOT)))
    return created


def sync_agents() -> list[str]:
    created: list[str] = []
    for agent_file in sorted((GROK / "agents").glob("*.md")):
        gh_name, cl_name = AGENT_MAP.get(agent_file.name, (agent_file.name, agent_file.stem))
        skill_path = GROK / "skills" / agent_file.stem / "SKILL.md"
        if not skill_path.exists():
            skill_path = GROK / "skills" / agent_file.stem.replace("-agent", "") / "SKILL.md"
        if not skill_path.exists() and agent_file.stem.endswith("-agent"):
            skill_path = GROK / "skills" / agent_file.stem / "SKILL.md"

        write_text(
            GITHUB / "agents" / gh_name,
            agent_to_github(agent_file, skill_path if skill_path.exists() else None),
        )
        write_text(
            CLAUDE / "agents" / f"{cl_name}.md",
            agent_to_claude(
                agent_file, cl_name, skill_path if skill_path.exists() else None
            ),
        )
        created.append(str((GITHUB / "agents" / gh_name).relative_to(ROOT)))
        created.append(str((CLAUDE / "agents" / f"{cl_name}.md").relative_to(ROOT)))

        # Thin agent skills also live under .github/skills for Copilot slash commands
        if agent_file.stem in AGENT_SKILLS or agent_file.name.replace(".md", "") in AGENT_SKILLS:
            sp = GROK / "skills" / agent_file.stem / "SKILL.md"
            if sp.exists():
                dest = GITHUB / "skills" / agent_file.stem / "SKILL.md"
                agent_skill = skill_to_github(sp, agent_file.stem)
                write_text(dest, agent_skill)
                created.append(str(dest.relative_to(ROOT)))
                write_copilot_skill(agent_file.stem, agent_skill, created)

            cmd_name = claude_command_name(agent_file.stem)
            if cmd_name and sp.exists():
                cmd_dest = CLAUDE / "commands" / f"{cmd_name}.md"
                write_text(cmd_dest, skill_to_claude_command(sp, cmd_name))
                created.append(str(cmd_dest.relative_to(ROOT)))
    return created


def sync_copilot_instructions() -> str:
    path = GITHUB / "copilot-instructions.md"
    write_text(path, build_copilot_instructions())
    return str(path.relative_to(ROOT))


def main() -> None:
    from _engine import manifest_sync as _manifest_sync

    all_created: list[str] = []
    all_created.extend(sync_skills())
    all_created.extend(sync_prompts())
    all_created.extend(sync_agents())
    all_created.append(sync_copilot_instructions())
    try:
        for rel in _manifest_sync.sync_manifests(ROOT):
            all_created.append(rel)
    except FileNotFoundError:
        pass  # deploy/bootstrap targets may ship a subset until first wave sync
    print(f"Synced {len(all_created)} files from .grok/ to .github/, .copilot/, and .claude/")
    # Per-file listing is agent-hostile (hundreds of lines). Skip when quiet.
    import os

    if os.environ.get("ORCHESTRATOR_QUIET", "").strip() not in ("1", "true", "yes"):
        for p in sorted(set(all_created)):
            print(f"  - {p}")


if __name__ == "__main__":
    main()