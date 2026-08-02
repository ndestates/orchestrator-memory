#!/usr/bin/env python3
"""
grade_run.py - Grader helper script for orchestrator skill-creator.

Adapted from the original Anthropic skill-creator grader for Grok/orchestrator.

Responsibilities:
- Collect transcript, output files, metrics, timing, user notes.
- Perform *programmatic* (deterministic) checks for assertions that can be auto-verified
  (file existence, simple string contains, basic counts, etc.).
- Prepare a ready-to-use grader prompt (injecting data) based on references/agents/grader.md.
- Write a draft or partial grading.json following the exact schema in references/schemas.md.
- Output a "grader_prompt.txt" that can be fed to spawn_subagent (or used inline).

This script handles the mechanical / auto-checkable parts so the LLM grader (via spawn_subagent
or direct reasoning in the skill) only does the hard evidence-based judgment and eval critique.

Usage examples:
  # From a run directory (recommended layout: .../eval-0/with_skill/outputs/)
  python -m scripts.grade_run --run-dir /path/to/iteration-1/eval-0/with_skill

  # Explicit
  python -m scripts.grade_run \
    --transcript transcript.md \
    --outputs-dir outputs/ \
    --expectations '["Output includes the name John", "File foo.txt exists"]' \
    --metrics metrics.json \
    --timing timing.json \
    --output grading.json

  # After manual or subagent grading, you can re-run with --merge-graded to combine.

The script writes:
- grading.json (partial or complete)
- grader_prompt.txt (full prompt ready for a grader subagent or the main agent)
- (optional) evidence_summary.json for debugging

No external deps beyond stdlib (to stay compatible with project constraints).
"""

import argparse
import json
import os
import re
import sys
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def find_project_root(start: Path) -> Path:
    """Walk up to find the project root (looks for .grok or .claude)."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".grok").is_dir() or (parent / ".claude").is_dir():
            return parent
    return current


def load_text_file(path: Path) -> str:
    """Safely read a text file."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR reading {path}: {e}]"


def list_outputs(outputs_dir: Path) -> Dict[str, Any]:
    """List files in outputs_dir and read text contents for small files."""
    if not outputs_dir.exists() or not outputs_dir.is_dir():
        return {"files": [], "contents": {}}

    files = []
    contents = {}
    for p in sorted(outputs_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(outputs_dir)
            files.append(str(rel))
            if p.suffix in {".txt", ".md", ".json", ".py", ".log", ".html", ".csv"} and p.stat().st_size < 500_000:
                contents[str(rel)] = load_text_file(p)[:10000]  # cap size

    return {"files": files, "contents": contents}


def simple_programmatic_check(expectation: str, transcript: str, outputs: Dict[str, Any]) -> Tuple[Optional[bool], Optional[str]]:
    """
    Attempt a deterministic check for an expectation.
    Returns (passed_or_none, evidence_or_none)
    Only returns a verdict for things we can confidently auto-check.
    """
    exp_lower = expectation.lower().strip()

    # File existence patterns
    file_match = re.search(r"file\s+['\"]?([\w./-]+)['\"]? (exists|is present|was created)", exp_lower)
    if file_match:
        fname = file_match.group(1)
        for f in outputs.get("files", []):
            if fname in f or f.endswith(fname):
                return True, f"File found in outputs: {f}"
        return False, f"No file matching '{fname}' found in outputs."

    # "contains" or "includes" text
    text_match = re.search(r"(includes|contains|has|shows)\s+['\"]?([^'\"]+)['\"]?", expectation, re.I)
    if text_match:
        needle = text_match.group(2).strip()
        if not needle:
            return None, None
        # Search transcript and output contents
        haystack = transcript + "\n" + "\n".join(outputs.get("contents", {}).values())
        if needle.lower() in haystack.lower():
            # Find a snippet for evidence
            idx = haystack.lower().find(needle.lower())
            start = max(0, idx - 30)
            end = min(len(haystack), idx + len(needle) + 30)
            snippet = haystack[start:end].replace("\n", " ")
            return True, f"Found in context: ...{snippet}..."
        else:
            return False, f"No evidence of '{needle}' in transcript or outputs."

    # Simple count patterns like "has 12 fields"
    count_match = re.search(r"(\d+)\s+(fields?|items?|rows?|lines?|files?)", exp_lower)
    if count_match:
        expected_num = int(count_match.group(1))
        unit = count_match.group(2)
        # Very naive: count occurrences of the unit word or files
        if "file" in unit:
            actual = len([f for f in outputs.get("files", []) if not f.endswith((".log",))])
        else:
            actual = len(re.findall(rf"\b{unit[:-1]}?\b", "\n".join(outputs.get("files", []))))  # rough
        if actual >= expected_num:
            return True, f"Counted approximately {actual} {unit} (expected {expected_num})"
        return False, f"Only found ~{actual} {unit}, expected {expected_num}"

    # "no errors" or success indicators
    if any(kw in exp_lower for kw in ["no error", "success", "completed without", "passed"]):
        if "error" not in transcript.lower() and "fail" not in transcript.lower():
            return True, "No error/failure indicators in transcript."
        return False, "Transcript mentions errors or failures."

    return None, None  # Cannot auto-check; needs LLM


def load_json_safe(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def build_grader_prompt(
    grader_prompt_template: str,
    expectations: List[str],
    transcript: str,
    outputs_dir: Path,
    outputs_info: Dict[str, Any],
    metrics: Dict[str, Any],
    timing: Dict[str, Any],
    user_notes: str,
) -> str:
    """Inject collected data into the grader prompt template."""
    # The original prompt expects the data to be described in the prompt.
    # We build a concrete instance.

    prompt = grader_prompt_template.strip() + "\n\n"

    prompt += "## Concrete Inputs for This Grading Run\n\n"

    prompt += f"**transcript_path**: (contents below)\n"
    prompt += f"**outputs_dir**: {outputs_dir}\n\n"

    prompt += "### Transcript\n```\n"
    prompt += transcript[:8000] + ("\n... (truncated)" if len(transcript) > 8000 else "")
    prompt += "\n```\n\n"

    prompt += "### Output Files Present\n"
    prompt += "\n".join(f"- {f}" for f in outputs_info.get("files", [])[:30]) or "(none)"
    prompt += "\n\n"

    if outputs_info.get("contents"):
        prompt += "### Key Output Contents (text files)\n"
        for fname, content in list(outputs_info["contents"].items())[:5]:
            prompt += f"**{fname}**:\n```\n{content[:2000]}\n```\n\n"

    prompt += "### Metrics (from metrics.json)\n```json\n"
    prompt += json.dumps(metrics, indent=2)[:1500] + "\n```\n\n"

    prompt += "### Timing (from timing.json)\n```json\n"
    prompt += json.dumps(timing, indent=2)[:800] + "\n```\n\n"

    if user_notes:
        prompt += f"### User Notes\n{user_notes}\n\n"

    prompt += "### Expectations to Grade\n"
    for i, exp in enumerate(expectations, 1):
        prompt += f"{i}. {exp}\n"
    prompt += "\n"

    prompt += (
        "Now follow the full process in the grader role above. "
        "Output ONLY valid JSON matching the grading.json schema (see references/schemas.md). "
        "Use the exact field names: expectations[].text, .passed, .evidence ; summary, claims, eval_feedback, etc.\n"
    )

    return prompt


def write_grading_json(
    path: Path,
    expectations: List[str],
    auto_results: List[Tuple[bool, str]],
    metrics: Dict,
    timing: Dict,
    user_notes: str,
) -> Dict[str, Any]:
    """Build and write a (partial) grading.json. LLM fills in the hard parts."""
    graded = []
    passed_count = 0
    for text, (auto_passed, evidence) in zip(expectations, auto_results):
        if auto_passed is not None:
            graded.append({
                "text": text,
                "passed": auto_passed,
                "evidence": evidence or "Programmatic check performed by grade_run.py"
            })
            if auto_passed:
                passed_count += 1
        else:
            graded.append({
                "text": text,
                "passed": None,  # marker for LLM to fill
                "evidence": "Needs LLM review (programmatic check inconclusive)"
            })

    total = len(expectations)
    summary = {
        "passed": passed_count,
        "failed": sum(1 for g in graded if g["passed"] is False),
        "total": total,
        "pass_rate": round(passed_count / max(1, total), 2) if total else 0.0,
        "needs_llm_review": sum(1 for g in graded if g["passed"] is None),
    }

    grading = {
        "expectations": graded,
        "summary": summary,
        "execution_metrics": metrics,
        "timing": timing,
        "claims": [],
        "user_notes_summary": {
            "uncertainties": [],
            "needs_review": [],
            "workarounds": [user_notes] if user_notes else [],
        },
        "eval_feedback": {
            "suggestions": [],
            "overall": "Auto-generated skeleton by grade_run.py. LLM grader should fill verdicts for non-programmatic items and provide critique."
        },
        "generated_by": "skill-creator/scripts/grade_run.py (orchestrator adaptation)",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(grading, indent=2))
    return grading


def main():
    parser = argparse.ArgumentParser(description="Grader helper for skill-creator (orchestrator port)")
    parser.add_argument("--run-dir", type=Path, help="Path to a run directory containing outputs/, transcript.md etc.")
    parser.add_argument("--transcript", type=Path, help="Path to transcript.md")
    parser.add_argument("--outputs-dir", type=Path, help="Directory with execution outputs")
    parser.add_argument("--expectations", type=str, help="JSON list of expectation strings, or path to evals.json")
    parser.add_argument("--metrics", type=Path, help="Path to metrics.json")
    parser.add_argument("--timing", type=Path, help="Path to timing.json")
    parser.add_argument("--user-notes", type=Path, help="Path to user_notes.md")
    parser.add_argument("--output", type=Path, default=Path("grading.json"), help="Where to write grading.json")
    parser.add_argument("--prompt-out", type=Path, default=Path("grader_prompt.txt"), help="Where to write the ready grader prompt")
    parser.add_argument("--grader-prompt", type=Path, default=None, help="Override path to grader.md template")

    args = parser.parse_args()

    root = find_project_root(Path.cwd())

    # Resolve paths
    if args.run_dir:
        run_dir = args.run_dir.resolve()
        transcript_path = args.transcript or (run_dir / "transcript.md")
        outputs_dir = args.outputs_dir or (run_dir / "outputs")
        metrics_path = args.metrics or (run_dir / "metrics.json")
        timing_path = args.timing or (run_dir / "timing.json")
        user_notes_path = args.user_notes or (run_dir / "user_notes.md")
    else:
        transcript_path = args.transcript or Path("transcript.md")
        outputs_dir = args.outputs_dir or Path("outputs")
        metrics_path = args.metrics
        timing_path = args.timing
        user_notes_path = args.user_notes

    transcript = load_text_file(transcript_path)
    outputs_info = list_outputs(outputs_dir)
    metrics = load_json_safe(metrics_path)
    timing = load_json_safe(timing_path)
    user_notes = load_text_file(user_notes_path) if user_notes_path else ""

    # Load expectations
    expectations: List[str] = []
    if args.expectations:
        exp_arg = args.expectations
        if exp_arg.endswith(".json") and Path(exp_arg).exists():
            data = json.loads(Path(exp_arg).read_text())
            if isinstance(data, dict):
                expectations = [e.get("prompt", str(e)) for e in data.get("evals", [])]
            elif isinstance(data, list):
                expectations = data
        else:
            try:
                expectations = json.loads(exp_arg)
            except json.JSONDecodeError:
                expectations = [exp_arg]
    if not expectations:
        # Fallback: look for evals.json near run
        for candidate in [outputs_dir.parent / "evals.json", Path("evals/evals.json"), Path("../evals.json")]:
            if candidate.exists():
                data = json.loads(candidate.read_text())
                expectations = [e.get("prompt", str(e)) for e in data.get("evals", [])]
                break

    if not expectations:
        print("WARNING: No expectations provided. Using placeholder.", file=sys.stderr)
        expectations = ["(no expectations provided - add via --expectations)"]

    # Programmatic checks
    auto_results = []
    for exp in expectations:
        verdict, evidence = simple_programmatic_check(exp, transcript, outputs_info)
        auto_results.append((verdict, evidence))

    # Load grader template
    grader_path = args.grader_prompt
    if not grader_path:
        grader_path = root / ".grok/skills/skill-creator/references/agents/grader.md"
        if not grader_path.exists():
            grader_path = Path(__file__).parent.parent / "references/agents/grader.md"

    grader_template = load_text_file(grader_path) or "# Grader prompt template not found. Using raw instructions.\n" + open(__file__).read()

    # Build prompt
    full_prompt = build_grader_prompt(
        grader_template,
        expectations,
        transcript,
        outputs_dir,
        outputs_info,
        metrics,
        timing,
        user_notes,
    )

    prompt_out = args.prompt_out.resolve() if args.prompt_out else Path("grader_prompt.txt")
    prompt_out.write_text(full_prompt)
    print(f"Wrote ready-to-use grader prompt to {prompt_out}")

    # Write grading skeleton
    grading = write_grading_json(
        args.output.resolve(),
        expectations,
        auto_results,
        metrics,
        timing,
        user_notes,
    )
    print(f"Wrote grading.json skeleton to {args.output}")

    # Summary
    print("\n=== grade_run.py summary ===")
    print(f"Expectations: {len(expectations)}")
    auto_checked = sum(1 for v, _ in auto_results if v is not None)
    print(f"Programmatically checked: {auto_checked}")
    print(f"Needs LLM review: {len(expectations) - auto_checked}")
    print("Next: Feed grader_prompt.txt to a subagent (spawn_subagent) or reason directly using the grader role.")
    print("Then complete/fix the grading.json with full evidence and eval_feedback.")


if __name__ == "__main__":
    main()
