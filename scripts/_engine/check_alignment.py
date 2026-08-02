"""Verify prompt/agent/skill name alignment (engine module)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from _engine.registry_compose import load_composed_registry
from _engine.roots import lazy_root

ROOT = lazy_root()
GROK_SKILLS = ROOT / ".grok/skills"
GROK_AGENTS = ROOT / ".grok/agents"
GROK_PROMPTS = ROOT / ".grok/prompts"
GITHUB_SKILLS = ROOT / ".github/skills"
COPILOT_SKILLS = ROOT / ".copilot/skills"
GITHUB_AGENTS = ROOT / ".github/agents"
GITHUB_PROMPTS = ROOT / ".github/prompts"
CLAUDE_COMMANDS = ROOT / ".claude/commands"
REGISTRY = ROOT / "chains/registry.yaml"  # composed output; load via load_composed_registry

# From sync_grok_to_github_claude.py
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
    "readme-specialist": "readme-specialist",
    "loop-triage": "loop-triage",
    "loop-verifier": "loop-verifier",
    "loop-engineering": "loop-engineering",
    "chain": "chain",
    "ddev-cleanup": "ddev-cleanup",
    "acquire-codebase-knowledge": "acquire-codebase-knowledge",
}

PROMPT_MAP = {
    "load-project-cache-first.md": "load-cache",
    "daily-standup-with-cache.md": "daily-standup",
    "read-codebase.md": "read-codebase",
    "model-schema-check.md": "model-schema-check",
    "filament-panel-review.md": "filament-panel-review",
    "amazon-ses-setup.md": "amazon-ses-setup",
    "aws-route53-dns-setup.md": "aws-route53-dns-setup",
    "paypal-integration.md": "paypal-integration",
}


def grok_skill_dirs() -> set[str]:
    dirs: set[str] = set()
    for skill in GROK_SKILLS.rglob("SKILL.md"):
        rel = skill.parent.relative_to(GROK_SKILLS)
        dirs.add(str(rel).replace("\\", "/") if str(rel) != "." else skill.parent.name)
    return dirs


def github_skill_dirs() -> set[str]:
    dirs: set[str] = set()
    for skill in GITHUB_SKILLS.rglob("SKILL.md"):
        rel = skill.parent.relative_to(GITHUB_SKILLS)
        dirs.add(str(rel).replace("\\", "/") if str(rel) != "." else skill.parent.name)
    return dirs


def copilot_skill_dirs() -> set[str]:
    dirs: set[str] = set()
    if not COPILOT_SKILLS.exists():
        return dirs
    for skill in COPILOT_SKILLS.rglob("SKILL.md"):
        rel = skill.parent.relative_to(COPILOT_SKILLS)
        dirs.add(str(rel).replace("\\", "/") if str(rel) != "." else skill.parent.name)
    return dirs


def resolve_invoke(invoke: str) -> bool:
    candidates = [
        GROK_SKILLS / invoke / "SKILL.md",
        GROK_PROMPTS / f"{invoke}.md",
        GROK_AGENTS / f"{invoke}.md",
        GITHUB_PROMPTS / f"{invoke}.prompt.md",
        GROK_SKILLS / "model-schema-check" / "SKILL.md",
    ]
    if "/" in invoke:
        candidates.append(GROK_SKILLS / invoke / "SKILL.md")
    return any(p.exists() for p in candidates)


def frontmatter_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(.+)$", text, re.M)
    return match.group(1).strip().strip('"') if match else None


def main() -> int:
    issues: list[str] = []

    reg = load_composed_registry(ROOT)

    skill_reg = reg
    for entry in skill_reg.get("skills", []):
        skill_path = ROOT / entry["path"]
        if not skill_path.exists():
            issues.append(f"skills registry missing file: {entry['id']} -> {entry['path']}")
    reg_dirs: set[str] = set()
    for entry in skill_reg.get("skills", []):
        skill_path = ROOT / entry["path"]
        rel = skill_path.parent.relative_to(GROK_SKILLS)
        reg_dirs.add(str(rel).replace("\\", "/") if str(rel) != "." else skill_path.parent.name)
    if "script-not-shell" not in reg_dirs:
        issues.append("skills registry missing required entry: script-not-shell")
    unregistered = sorted(grok_skill_dirs() - reg_dirs - {"copilot-instructions"})
    for skill_id in unregistered:
        issues.append(f"grok skill dir not in chains/registry.yaml skills: {skill_id}")
    if unregistered:
        issues.append(
            "hint: run python3 scripts/register-project-skills.py "
            "(auto-run after deploy-template-wave.sh on wave apps)"
        )
    for chain in reg["chains"]:
        for step in chain["steps"]:
            inv = step["invoke"]
            if not resolve_invoke(inv):
                issues.append(f"chain invoke unresolved: {inv} (chain {chain['id']})")

    # copilot-instructions syncs to .github/copilot-instructions.md, not skills/
    grok_only = grok_skill_dirs() - github_skill_dirs() - {"copilot-instructions"}
    missing_gh = sorted(grok_only)
    if missing_gh:
        issues.append(f"grok skills missing in .github: {missing_gh}")

    # .copilot/skills/ mirrors .github/skills/ (except copilot-instructions → copilot-instructions.md)
    copilot_only = grok_skill_dirs() - copilot_skill_dirs() - {"copilot-instructions"}
    if copilot_only:
        issues.append(f"grok skills missing in .copilot/skills: {sorted(copilot_only)}")
    if (GROK_SKILLS / "copilot-instructions" / "SKILL.md").exists():
        if not (ROOT / ".github/copilot-instructions.md").exists():
            issues.append("copilot-instructions missing .github/copilot-instructions.md target")

    for skill_dir, cmd in SKILL_COMMAND_MAP.items():
        cmd_path = CLAUDE_COMMANDS / f"{cmd}.md"
        if not cmd_path.exists():
            issues.append(f"SKILL_COMMAND_MAP: {skill_dir} -> {cmd}.md missing in .claude/commands")

    for prompt_file, cmd in PROMPT_MAP.items():
        cmd_path = CLAUDE_COMMANDS / f"{cmd}.md"
        gh_prompt = GITHUB_PROMPTS / prompt_file.replace(".md", ".prompt.md")
        if not cmd_path.exists():
            issues.append(f"PROMPT_MAP: {prompt_file} -> {cmd}.md missing in .claude/commands")
        if not gh_prompt.exists():
            issues.append(f"PROMPT_MAP: {gh_prompt.name} missing in .github/prompts")

    for skill_dir in sorted(grok_skill_dirs()):
        if "/" in skill_dir:
            grok_path = GROK_SKILLS / skill_dir / "SKILL.md"
            gh_path = GITHUB_SKILLS / skill_dir / "SKILL.md"
        else:
            grok_path = GROK_SKILLS / skill_dir / "SKILL.md"
            gh_path = GITHUB_SKILLS / skill_dir / "SKILL.md"
        if not grok_path.exists() or not gh_path.exists():
            continue
        gn, hn = frontmatter_name(grok_path), frontmatter_name(gh_path)
        if gn and hn and gn != hn:
            issues.append(f"frontmatter name mismatch: {skill_dir} grok={gn} github={hn}")

    grok_agent_names = {p.stem for p in GROK_AGENTS.glob("*.md")}
    gh_agent_stems = set()
    for p in GITHUB_AGENTS.glob("*.md"):
        gh_agent_stems.add(p.name.replace(".agent.md", "").replace(".md", ""))

    for agent in sorted(grok_agent_names):
        if agent not in gh_agent_stems:
            issues.append(f"grok agent missing in .github/agents: {agent}")

    print("Name alignment check")
    print(
        f"Grok skills: {len(grok_skill_dirs())} | GitHub: {len(github_skill_dirs())} | Copilot: {len(copilot_skill_dirs())}"
    )
    print(f"Grok agents: {len(grok_agent_names)} | GitHub agents: {len(gh_agent_stems)}")
    print(f"Claude commands: {len(list(CLAUDE_COMMANDS.glob('*.md')))}")

    if issues:
        print(f"\nFAIL — {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("\nPASS — all chain invokes, skill dirs, maps, and frontmatter names aligned")
    return 0


if __name__ == "__main__":
    sys.exit(main())