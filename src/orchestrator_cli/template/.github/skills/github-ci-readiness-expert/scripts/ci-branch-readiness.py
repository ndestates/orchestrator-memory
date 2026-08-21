#!/usr/bin/env python3
"""Analyse current branch vs GitHub Actions workflows — predict CI triggers and gaps."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("error: PyYAML required", file=sys.stderr)
    sys.exit(1)

SECRET_REF = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")
VAR_REF = re.compile(r"\$\{\{\s*vars\.([A-Za-z0-9_]+)\s*\}\}")
ENV_REF = re.compile(r"\$\{\{\s*env\.([A-Za-z0-9_]+)\s*\}\}")


@dataclass
class WorkflowTrigger:
    workflow: str
    event: str
    detail: str
    will_run: bool


@dataclass
class ReadinessReport:
    project_root: str
    project_slug: str
    branch: str
    pr_target: str
    timestamp: str
    workflows_total: int
    triggers_on_push: list[dict[str, Any]] = field(default_factory=list)
    triggers_on_pr: list[dict[str, Any]] = field(default_factory=list)
    secret_refs: list[str] = field(default_factory=list)
    missing_secrets: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    node24_errors: list[str] = field(default_factory=list)
    local_checks: list[dict[str, str]] = field(default_factory=list)
    verdict: str = "UNKNOWN"
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except OSError as exc:
        return 1, "", str(exc)


def current_branch(root: Path) -> str:
    code, out, _ = run_cmd(["git", "branch", "--show-current"], root)
    if code != 0 or not out:
        return "HEAD"
    return out


def workflow_on_block(data: dict[str, Any]) -> dict[str, Any]:
    if "on" in data:
        return data["on"] if isinstance(data["on"], dict) else {}
    if True in data:
        val = data[True]
        return val if isinstance(val, dict) else {}
    return {}


def glob_branch_match(pattern: str, branch: str) -> bool:
    if pattern == branch:
        return True
    norm = pattern.replace("**", "*")
    return fnmatch.fnmatch(branch, norm) or fnmatch.fnmatch(branch, pattern)


def push_triggers(on: dict[str, Any], branch: str) -> tuple[bool, str]:
    push = on.get("push")
    if push is None:
        return False, "no push trigger"
    if push is True or push is None:
        return True, "push (all branches)"
    if isinstance(push, dict):
        branches = push.get("branches")
        paths = push.get("paths")
        if not branches:
            detail = "push (all branches)"
            if paths:
                detail += f"; path filter: {paths}"
            return True, detail
        matched = [b for b in branches if glob_branch_match(str(b), branch)]
        if matched:
            detail = f"push branches {matched}"
            if paths:
                detail += f"; path filter: {paths}"
            return True, detail
        return False, f"push branches {branches} — no match for {branch}"
    return False, "push config unrecognized"


def pr_triggers(on: dict[str, Any], source_branch: str, target: str) -> tuple[bool, str]:
    pr = on.get("pull_request")
    if pr is None:
        return False, "no pull_request trigger"
    if pr is True:
        return True, f"pull_request (any target)"
    if isinstance(pr, dict):
        branches = pr.get("branches")
        paths = pr.get("paths")
        if branches:
            matched = [b for b in branches if glob_branch_match(str(b), target)]
            if not matched:
                return False, f"pull_request target branches {branches} — no match for {target}"
            detail = f"pull_request → {target} (allowed targets {matched})"
        else:
            detail = f"pull_request → {target}"
        if paths:
            detail += f"; path filter: {paths}"
        return True, detail
    return False, "pull_request config unrecognized"


def load_workflows(root: Path) -> list[tuple[str, dict[str, Any], str]]:
    wf_dir = root / ".github" / "workflows"
    out: list[tuple[str, dict[str, Any], str]] = []
    if not wf_dir.is_dir():
        return out
    for path in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            out.append((path.name, {}, f"YAML error: {exc}"))
            continue
        if isinstance(data, dict):
            out.append((path.name, data, text))
    return out


def collect_secret_refs(text: str) -> set[str]:
    return set(SECRET_REF.findall(text))


def gh_secret_names(root: Path) -> set[str] | None:
    code, out, err = run_cmd(["gh", "secret", "list", "--json", "name", "-q", ".[].name"], root)
    if code != 0:
        return None
    names = {line.strip() for line in out.splitlines() if line.strip()}
    return names


def validate_workflows(root: Path) -> list[str]:
    script = root / ".grok/skills/github-workflow-expert/scripts/workflow-validate.sh"
    if not script.is_file():
        script = root / ".grok/skills/github-ci-readiness-expert/scripts/workflow-validate-lite.sh"
    if script.is_file():
        code, out, err = run_cmd(["bash", str(script)], root)
        if code != 0:
            return (err or out).splitlines() or ["workflow validation failed"]
        return []
    errors: list[str] = []
    for name, data, _ in load_workflows(root):
        if not data:
            errors.append(f"{name}: invalid YAML")
    return errors


def verify_node24(root: Path) -> list[str]:
    script = root / "scripts/verify_github_actions_node24.py"
    if not script.is_file():
        return []
    code, out, err = run_cmd([sys.executable, str(script)], root)
    if code != 0:
        return (out + "\n" + err).splitlines()
    return []


def run_local_parity(root: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for label, cmd in [
        ("chain-audit", ["bash", "scripts/chain-audit.sh"]),
        ("node24-verify", [sys.executable, "scripts/verify_github_actions_node24.py"]),
    ]:
        rel_cmd = cmd[1] if cmd[0] == "bash" else cmd[1]
        if cmd[0] == "bash" and not (root / "scripts/chain-audit.sh").is_file():
            continue
        if rel_cmd.endswith(".py") and not (root / rel_cmd).is_file():
            continue
        code, out, err = run_cmd(cmd, root)
        checks.append(
            {
                "check": label,
                "exit_code": str(code),
                "status": "PASS" if code == 0 else "FAIL",
                "tail": "\n".join((out + "\n" + err).splitlines()[-5:]),
            }
        )
    return checks


def project_slug(root: Path, override: str | None) -> str:
    if override:
        return override
    return root.name


def specialization_path(root: Path, slug: str, refs_root: Path | None = None) -> Path | None:
    bases = [root]
    if refs_root and refs_root.resolve() != root.resolve():
        bases.append(refs_root)
    rel_dir = Path(".grok/skills/github-ci-readiness-expert/references")
    for base in bases:
        candidates = [
            base / rel_dir / f"{slug}-ci.md",
            base / rel_dir / "generic-laravel-ci.md",
        ]
        for path in candidates:
            if path.is_file():
                return path
    return None


def compute_verdict(report: ReadinessReport) -> None:
    blockers: list[str] = []
    warnings: list[str] = list(report.warnings)

    if report.validation_errors:
        blockers.append("workflow YAML validation failed")
    if report.node24_errors:
        blockers.append("Node 24 / action pin policy failed")
    if report.missing_secrets:
        blockers.extend([f"missing secret: {s}" for s in report.missing_secrets[:5]])

    push_or_pr = report.triggers_on_push or report.triggers_on_pr
    if not push_or_pr:
        warnings.append("no workflows predicted for push or PR to develop on this branch")

    for check in report.local_checks:
        if check.get("status") == "FAIL":
            blockers.append(f"local check failed: {check.get('check')}")

    report.blockers = blockers
    report.warnings = warnings
    if blockers:
        report.verdict = "BLOCKED"
    elif warnings:
        report.verdict = "CONDITIONAL"
    else:
        report.verdict = "READY"


def analyse(
    root: Path,
    branch: str,
    pr_target: str,
    slug: str | None,
    refs_root: Path | None = None,
) -> ReadinessReport:
    slug = project_slug(root, slug)
    report = ReadinessReport(
        project_root=str(root),
        project_slug=slug,
        branch=branch,
        pr_target=pr_target,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        workflows_total=0,
    )

    workflows = load_workflows(root)
    report.workflows_total = len(workflows)

    all_secret_refs: set[str] = set()
    for name, data, text in workflows:
        if not data:
            report.validation_errors.append(f"{name}: empty or invalid")
            continue
        all_secret_refs |= collect_secret_refs(text)
        on = workflow_on_block(data)
        push_run, push_detail = push_triggers(on, branch)
        if push_run:
            report.triggers_on_push.append({"workflow": name, "detail": push_detail})
        pr_run, pr_detail = pr_triggers(on, branch, pr_target)
        if pr_run:
            report.triggers_on_pr.append({"workflow": name, "detail": pr_detail})

    report.secret_refs = sorted(all_secret_refs)
    gh_secrets = gh_secret_names(root)
    if gh_secrets is not None and all_secret_refs:
        report.missing_secrets = sorted(all_secret_refs - gh_secrets)
    elif all_secret_refs and gh_secrets is None:
        report.warnings.append("gh secret list unavailable — secret gap check skipped")

    report.validation_errors = validate_workflows(root)
    report.node24_errors = verify_node24(root)
    report.local_checks = run_local_parity(root)

    spec = specialization_path(root, slug, refs_root)
    if spec:
        try:
            spec_rel = str(spec.relative_to(root))
        except ValueError:
            spec_rel = str(spec)
        report.warnings.append(f"specialization: {spec_rel}")
    else:
        report.warnings.append(f"no CI specialization for slug={slug}; using rubric only")

    compute_verdict(report)
    return report


def write_markdown(report: ReadinessReport, out_path: Path) -> None:
    lines = [
        f"# CI Branch Readiness — {report.timestamp}",
        "",
        f"**Project:** `{report.project_slug}`",
        f"**Branch:** `{report.branch}`",
        f"**PR target:** `{report.pr_target}`",
        f"**Verdict:** **{report.verdict}**",
        "",
        "## Workflows on push",
    ]
    if report.triggers_on_push:
        for t in report.triggers_on_push:
            lines.append(f"- `{t['workflow']}` — {t['detail']}")
    else:
        lines.append("- (none predicted)")
    lines.extend(["", "## Workflows on PR", ""])
    if report.triggers_on_pr:
        for t in report.triggers_on_pr:
            lines.append(f"- `{t['workflow']}` — {t['detail']}")
    else:
        lines.append("- (none predicted)")
    if report.blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {b}" for b in report.blockers)
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {w}" for w in report.warnings)
    if report.missing_secrets:
        lines.extend(["", "## Missing secrets (names only)", ""])
        lines.extend(f"- `{s}`" for s in report.missing_secrets)
    lines.extend(["", "## Local parity", ""])
    for c in report.local_checks:
        lines.append(f"- {c['check']}: {c['status']} (exit {c['exit_code']})")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--branch", default="")
    parser.add_argument("--pr-target", default="develop")
    parser.add_argument("--slug", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument(
        "--refs-root",
        type=Path,
        default=None,
        help="Orchestrator root for references when skill not yet deployed on target",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    branch = args.branch or current_branch(root)
    refs_root = args.refs_root.resolve() if args.refs_root else None
    report = analyse(root, branch, args.pr_target, args.slug or None, refs_root)

    if args.write_report:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out = root / "reports" / "ci" / f"{date}-{report.project_slug}-branch-readiness.md"
        write_markdown(report, out)
        print(f"report: {out}")

    payload = asdict(report)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"ci-branch-readiness: {report.verdict}")
        print(f"  branch={branch} slug={report.project_slug}")
        print(f"  push workflows: {len(report.triggers_on_push)} | pr workflows: {len(report.triggers_on_pr)}")
        if report.blockers:
            print("  blockers:")
            for b in report.blockers:
                print(f"    - {b}")

    return 0 if report.verdict != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())