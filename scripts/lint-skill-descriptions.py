#!/usr/bin/env python3
"""Lint (and optionally fix) SKILL.md frontmatter description length.

Grok Build injects every discovered skill as:

  - name: <description>

into synthetic system_reminder messages. Long descriptions multiply by skill
count and, when the host re-injects each turn, can blow past the context budget
(observed ~1.1M tokens with ~54KB catalogs × many turns).

Policy (token_policy.skill_description_max_chars, default 220):
  - description = short trigger only (what + when), not the full skill body
  - put procedure detail in the SKILL.md body, not the description
  - optional when-to-use may hold extra triggers (not all hosts inject it)

Exit 0 clean; 1 on violations (unless --fix rewrites and cleans).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
DEFAULT_MAX = 220
SKILL_GLOB = ".grok/skills/**/SKILL.md"

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


def _load_max_chars(root: Path, cli_max: int | None) -> int:
    if cli_max is not None:
        return cli_max
    manifest = root / ".github" / "project-manifest.yaml"
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"skill_description_max_chars:\s*(\d+)", text)
        if m:
            return int(m.group(1))
    return DEFAULT_MAX


def _parse_frontmatter(text: str) -> tuple[dict | None, str, str]:
    """Return (data_or_None, fm_raw, body). data is best-effort yaml."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "", text
    fm_raw = m.group(1)
    body = text[m.end() :]
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(fm_raw) or {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    return data, fm_raw, body


def _first_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    # Split on sentence end, keep Use when / Use on clause preference
    m = re.search(r"(.+?[.!?])(\s|$)", text)
    if m and len(m.group(1)) >= 40:
        return m.group(1).strip()
    return text


def shorten_description(desc: str, max_chars: int) -> str:
    """Produce a budget-compliant description without inventing new meaning."""
    desc = re.sub(r"\s+", " ", (desc or "").strip())
    if len(desc) <= max_chars:
        return desc

    # Prefer first sentence if it fits
    first = _first_sentence(desc)
    if 40 <= len(first) <= max_chars:
        return first

    # Prefer "…. Use when/on …" shortened: take head + use-when clause if short
    use_m = re.search(r"(Use when[:\s].+)$", desc, re.I)
    head = first if len(first) < len(desc) else desc
    if use_m:
        use = use_m.group(1).strip()
        # Build head without trailing use clause
        head_only = desc[: use_m.start()].strip().rstrip(".;")
        head_only = _first_sentence(head_only) if head_only else head
        candidate = f"{head_only} {use}".strip()
        if len(candidate) <= max_chars:
            return candidate
        # Cap head then add abbreviated use
        budget_head = max_chars - min(len(use) + 1, max_chars // 3)
        if budget_head >= 40:
            h = _truncate_words(head_only, budget_head)
            rem = max_chars - len(h) - 1
            if rem >= 20:
                return f"{h} {_truncate_words(use, rem)}"
            return h

    return _truncate_words(desc, max_chars)


def _truncate_words(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return "…"
    cut = text[: max_chars - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def _rewrite_frontmatter_description(fm_raw: str, new_desc: str) -> str:
    """Replace description value in raw frontmatter; preserve other fields."""
    lines = fm_raw.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^description:\s*", ln) and not replaced:
            # Consume block or inline description
            inline = re.match(r"^description:\s*(.*)$", ln)
            assert inline
            rest = inline.group(1)
            i += 1
            if rest.strip() in ("", ">", "|", ">-", ">|", "|-", "|+"):
                # folded/block: skip indented continuation lines
                while i < len(lines):
                    cont = lines[i]
                    if cont.startswith(" ") or cont.startswith("\t") or cont.strip() == "":
                        # blank only if still in block — stop on next key
                        if cont.strip() == "" and i + 1 < len(lines):
                            nxt = lines[i + 1]
                            if re.match(r"^[a-zA-Z0-9_-]+:", nxt):
                                break
                        if cont.startswith(" ") or cont.startswith("\t"):
                            i += 1
                            continue
                        if cont.strip() == "":
                            i += 1
                            continue
                    if re.match(r"^[a-zA-Z0-9_-]+:", cont):
                        break
                    # unexpected non-indented non-key — break
                    break
            # Always quote — descriptions often contain ":", "&", quotes
            out.append(_format_description_line(new_desc))
            replaced = True
            continue
        out.append(ln)
        i += 1
    if not replaced:
        # insert after name: if present, else at top
        inserted = False
        final: list[str] = []
        for ln in out:
            final.append(ln)
            if not inserted and re.match(r"^name:\s*", ln):
                final.append(_format_description_line(new_desc))
                inserted = True
        if not inserted:
            final.insert(0, _format_description_line(new_desc))
        out = final
    return "".join(out)


def _format_description_line(desc: str) -> str:
    """YAML-safe description field (single-line double-quoted)."""
    desc = re.sub(r"\s+", " ", desc.strip())
    # Escape for double-quoted YAML scalar
    escaped = (
        desc.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    return f'description: "{escaped}"\n'


def scan_skill(path: Path, max_chars: int) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    data, fm_raw, body = _parse_frontmatter(text)
    if data is None:
        return {
            "file": str(path),
            "severity": "warn",
            "rule": "no-frontmatter",
            "length": 0,
            "max": max_chars,
            "description": "",
        }
    desc = data.get("description") or ""
    if not isinstance(desc, str):
        desc = str(desc)
    desc = re.sub(r"\s+", " ", desc.strip())
    if len(desc) <= max_chars:
        return None
    return {
        "file": str(path),
        "severity": "critical",
        "rule": "description-too-long",
        "length": len(desc),
        "max": max_chars,
        "description": desc,
        "suggested": shorten_description(desc, max_chars),
        "fm_raw": fm_raw,
        "body": body,
        "full_text": text,
    }


def fix_skill(finding: dict) -> None:
    path = Path(finding["file"])
    new_desc = finding["suggested"]
    new_fm = _rewrite_frontmatter_description(finding["fm_raw"], new_desc)
    # Always separate closing --- from last frontmatter line
    body = finding["body"].lstrip("\n")
    path.write_text(
        "---\n" + new_fm.rstrip() + "\n---\n" + body,
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    ap.add_argument("--max-chars", type=int, default=None, help="override budget")
    ap.add_argument("--fix", action="store_true", help="rewrite long descriptions")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="optional specific SKILL.md paths (default: .grok/skills/**)",
    )
    args = ap.parse_args()
    root: Path = args.root.resolve()
    max_chars = _load_max_chars(root, args.max_chars)

    paths: list[Path] = []
    if args.paths:
        paths = [Path(p) if Path(p).is_absolute() else root / p for p in args.paths]
    else:
        paths = sorted(root.glob(SKILL_GLOB))

    findings: list[dict] = []
    for path in paths:
        if not path.is_file():
            continue
        f = scan_skill(path, max_chars)
        if f:
            findings.append(f)

    fixed = 0
    if args.fix:
        for f in findings:
            if f.get("rule") != "description-too-long":
                continue
            fix_skill(f)
            fixed += 1
        # re-scan
        findings = []
        for path in paths:
            if path.is_file():
                f = scan_skill(path, max_chars)
                if f:
                    findings.append(f)

    critical = [f for f in findings if f.get("severity") == "critical"]
    payload = {
        "max_chars": max_chars,
        "scanned": len(paths),
        "findings": [
            {k: v for k, v in f.items() if k not in ("fm_raw", "body", "full_text")}
            for f in findings
        ],
        "fixed": fixed,
        "status": "PASS" if not critical else "FAIL",
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"skill description budget: max_chars={max_chars}")
        print(f"scanned: {len(paths)}  fixed: {fixed}  violations: {len(critical)}")
        for f in critical[:50]:
            rel = f["file"]
            try:
                rel = str(Path(f["file"]).resolve().relative_to(root))
            except Exception:
                pass
            print(f"  FAIL {rel}: {f['length']} > {f['max']}")
            if f.get("suggested"):
                print(f"       → {f['suggested'][:120]}")
        if len(critical) > 50:
            print(f"  … {len(critical) - 50} more")
        print(f"Status: {payload['status']}")

    return 0 if not critical else 1


if __name__ == "__main__":
    sys.exit(main())
