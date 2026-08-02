#!/usr/bin/env python3
"""Session-start situation brief — where we are, what is in flight, repetition gate.

Session-start MUST understand project context and the latest situation. This script
builds a capped report from:

  - resume card (done / open / next)
  - latest TODO open items
  - STATE.md open/done spine
  - vault lessons + precedents for open work
  - wiki index / open-questions keyword hits (when wiki lean|full)

When open work looks already done (vault/wiki/STATE/resume), emit a **repetition**
block so the agent reminds the user and asks:

  [use prior | continue | re-scope]

Usage:
  python3 scripts/session-situation-brief.py
  python3 scripts/session-situation-brief.py --json
  python3 scripts/session-situation-brief.py --write
  python3 scripts/session-situation-brief.py --use-cache   # skip rebuild if inputs unchanged

Exit 0 always (report-only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts._engine import vault as vault_mod
    from scripts._engine import vault_query as vault_query_mod
except ImportError:
    try:
        from _engine import vault as vault_mod  # type: ignore
        from _engine import vault_query as vault_query_mod  # type: ignore
    except ImportError:
        vault_mod = None  # type: ignore
        vault_query_mod = None  # type: ignore

SESSIONS = ROOT / "reports" / "sessions"
LEDGER = ROOT / "reports" / "vault" / "events.jsonl"
SITUATION_JSON = SESSIONS / "situation-latest.json"
SITUATION_TXT = SESSIONS / "situation-latest.txt"
SITUATION_FP = SESSIONS / "situation-fingerprint.txt"
# Max age for cache hit even if fingerprint matches (seconds)
CACHE_MAX_AGE = 3600
STOP = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "when",
        "then",
        "into",
        "only",
        "after",
        "before",
        "using",
        "via",
        "run",
        "add",
        "use",
        "set",
        "get",
        "not",
        "any",
        "all",
        "new",
        "old",
        "if",
        "or",
        "to",
        "of",
        "in",
        "on",
        "a",
        "an",
        "is",
        "are",
        "be",
        "as",
        "at",
        "by",
        "it",
        "we",
        "do",
        "does",
        "done",
        "work",
        "item",
        "todo",
        "p0",
        "p1",
        "p2",
        "p3",
    }
)


def _run(cmd: list[str], *, timeout: int = 45) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode, (r.stdout or "").strip()
    except Exception as exc:
        return 1, str(exc)


def _read(path: Path, limit: int = 0) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if limit and len(text) > limit:
        return text[:limit]
    return text


def _git_branch() -> str:
    code, out = _run(["git", "branch", "--show-current"])
    return out if code == 0 else "unknown"


def _template_version() -> str:
    for name in ("VERSION", "version"):
        p = ROOT / name
        if p.is_file():
            line = _read(p).strip().splitlines()
            if line:
                return line[0].strip()
    return "?"


def _behind_develop() -> str:
    code, out = _run(["git", "rev-list", "--count", "HEAD..origin/develop"])
    return out if code == 0 and out.isdigit() else "?"


def _resume_branch_kv() -> dict[str, str]:
    script = ROOT / "scripts" / "resume-branch.sh"
    if not script.is_file():
        return {}
    code, out = _run(["bash", str(script)], timeout=90)
    if code != 0 or not out:
        return {}
    kv: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            kv[k.strip()] = v.strip()
    return kv


def _latest_resume() -> Path | None:
    if not SESSIONS.is_dir():
        return None
    resumes = sorted(SESSIONS.glob("resume-*.md"), key=lambda p: p.name, reverse=True)
    return resumes[0] if resumes else None


def _parse_resume_card(path: Path | None) -> dict[str, Any]:
    if not path or not path.is_file():
        return {"status": "missing", "path": None, "open": [], "done": [], "next": [], "card": ""}
    text = _read(path, 12000)
    card_lines: list[str] = []
    in_card = False
    for line in text.splitlines():
        if line.startswith("# Session resume"):
            in_card = True
            continue
        if in_card and line.startswith("## "):
            break
        if in_card and line.strip():
            card_lines.append(line)
    card = "\n".join(card_lines).strip()

    open_items: list[str] = []
    done_items: list[str] = []
    next_items: list[str] = []
    section = ""
    for line in text.splitlines():
        if line.startswith("## Open"):
            section = "open"
            continue
        if line.startswith("## Next"):
            section = "next"
            continue
        if line.startswith("## Done"):
            section = "done"
            continue
        if line.startswith("## "):
            section = ""
            continue
        m = re.match(r"^[-*]\s+(?:\[.\]\s+)?(.+)$", line.strip())
        if not m:
            continue
        body = m.group(1).strip()
        if body.startswith("(") and "none" in body.lower():
            continue
        if section == "open":
            open_items.append(body[:180])
        elif section == "done":
            done_items.append(body[:180])
        elif section == "next":
            next_items.append(body[:180])

    # Fallback: compact card "Open (from TODO…):" line
    if not open_items:
        for line in card_lines:
            if line.lower().startswith("open"):
                body = line.split(":", 1)[-1].strip()
                if body and body != "—":
                    open_items = [p.strip() for p in re.split(r";\s*", body) if p.strip()][:8]
            if line.lower().startswith("done this session"):
                body = line.split(":", 1)[-1].strip()
                if body and body not in ("—", "-"):
                    # strip (1) prefixes
                    parts = re.split(r";\s*", body)
                    for p in parts:
                        p = re.sub(r"^\(\d+\)\s*", "", p).strip()
                        if p:
                            done_items.append(p[:180])

    branch = ""
    for line in card_lines:
        m = re.match(r"^Branch:\s*([^\s(]+)", line)
        if m:
            branch = m.group(1)
            break

    return {
        "status": "found",
        "path": str(path.relative_to(ROOT)),
        "card": card,
        "branch": branch,
        "open": open_items[:8],
        "done": done_items[:8],
        "next": next_items[:6],
    }


def _latest_todo() -> Path | None:
    todo_dir = ROOT / "TODO"
    if not todo_dir.is_dir():
        return None
    dated: list[tuple[str, Path]] = []
    for path in todo_dir.glob("*_TODO.md"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
        if m:
            dated.append((m.group(1), path))
    if not dated:
        return None
    dated.sort(key=lambda x: x[0], reverse=True)
    # Prefer plain YYYY-MM-DD_TODO.md for same day
    by_day: dict[str, list[Path]] = {}
    for d, p in dated:
        by_day.setdefault(d, []).append(p)
    day = dated[0][0]
    pool = by_day[day]
    plain = [p for p in pool if re.match(r"\d{4}-\d{2}-\d{2}_TODO\.md$", p.name)]
    return plain[0] if plain else sorted(pool, key=lambda p: len(p.name), reverse=True)[0]


def _todo_open(path: Path | None, limit: int = 10) -> list[str]:
    if not path or not path.is_file():
        return []
    items: list[str] = []
    for line in _read(path).splitlines():
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+\[\s*\]\s+(.+)$", line)
        if not m:
            continue
        body = m.group(1).strip()
        if re.search(r"do not re-plan|standing rules", body, re.I):
            continue
        items.append(body[:180])
        if len(items) >= limit:
            break
    return items


def _state_snippets() -> dict[str, list[str]]:
    path = ROOT / "STATE.md"
    if not path.is_file():
        return {"open": [], "done": [], "facts": []}
    text = _read(path, 20000)
    section = ""
    open_i: list[str] = []
    done_i: list[str] = []
    facts: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip().lower()
            if "open" in title:
                section = "open"
            elif "done" in title:
                section = "done"
            elif "verified" in title or "fact" in title:
                section = "facts"
            else:
                section = ""
            continue
        m = re.match(r"^\s*[-*]\s+(?:\[.\]\s+)?(.+)$", line)
        if not m:
            continue
        body = m.group(1).strip()[:160]
        if section == "open" and "[x]" not in line.lower() and "[X]" not in line:
            # only unchecked if checklist; else include
            if re.search(r"\[\s*\]", line) or not re.search(r"\[.\]", line):
                open_i.append(body)
        elif section == "done":
            done_i.append(body)
        elif section == "facts":
            facts.append(body)
    return {
        "open": open_i[:6],
        "done": done_i[:8],
        "facts": facts[:6],
    }


def _workstream_primary() -> str:
    reg = SESSIONS / "workstreams.yaml"
    if not reg.is_file():
        return ""
    m = re.search(r"(?m)^\s*primary:\s*[\"']?([^\s\"'#]+)", _read(reg))
    return m.group(1).strip() if m else ""


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-_/]{2,}", text.lower())
    return {w for w in words if w not in STOP and not w.isdigit()}


def _overlap_score(a: str, b: str) -> float:
    """Hybrid of set-overlap and bag-of-words cosine (stdlib; no vector DB)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    jacc = len(inter) / max(1, min(len(ta), len(tb)))
    # BOW cosine — helps light paraphrases without embeddings
    from collections import Counter
    import math

    ca, cb = Counter(ta), Counter(tb)
    keys = set(ca) | set(cb)
    dot = sum(ca[k] * cb[k] for k in keys)
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    cos = (dot / (na * nb)) if na and nb else 0.0
    return max(jacc, 0.85 * cos)


def _vault_lessons(limit: int = 5) -> list[dict[str, Any]]:
    if vault_mod is None or not LEDGER.is_file():
        return []
    try:
        events = vault_mod.load_events(LEDGER)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for ev in reversed(events):
        if ev.get("type") not in (
            "lesson",
            "synthesis",
            "codebase_knowledge",
            "precedent",
            "fix",
            "outcome",
        ):
            continue
        p = ev.get("payload") or {}
        text = ""
        for k in ("text", "summary", "lesson", "message"):
            if p.get(k):
                text = str(p[k]).strip()
                break
        if not text:
            continue
        safe, _ = vault_mod.scrub_for_ai_context(text)
        out.append(
            {
                "type": ev.get("type"),
                "text": safe[:220],
                "hash": (ev.get("content_hash") or "")[:12],
                "source": ev.get("source"),
            }
        )
        if len(out) >= limit:
            break
    return out


def _vault_precedents(query: str, limit: int = 4) -> list[dict[str, Any]]:
    if not query or vault_query_mod is None or not LEDGER.is_file():
        return []
    try:
        res = vault_query_mod.query_precedents(
            query, ledger_path=LEDGER, limit=limit, build_chain=False
        )
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for p in res.get("precedents") or []:
        judgment = p.get("judgment") or p.get("text") or ""
        if isinstance(judgment, dict):
            judgment = json.dumps(judgment)
        out.append(
            {
                "judgment": str(judgment)[:200],
                "score": p.get("score") or p.get("similarity"),
                "type": p.get("type"),
            }
        )
    return out


def _wiki_hits(open_items: list[str], limit: int = 5) -> list[dict[str, str]]:
    wiki_index = ROOT / "wiki" / "index.md"
    open_q = ROOT / "wiki" / "open-questions.md"
    if not wiki_index.is_file():
        return []
    corpus: list[tuple[str, str]] = []
    for path in (wiki_index, open_q):
        if not path.is_file():
            continue
        for line in _read(path).splitlines():
            # table rows or bullets with links
            m = re.search(r"\[([^\]]+)\]\(([^)]+)\)\s*\|?\s*(.*)$", line)
            if m:
                title, rel, summary = m.group(1), m.group(2), m.group(3).strip()
                corpus.append((f"{title} {summary}", f"wiki/{rel.lstrip('./')}"))
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                corpus.append((line.strip()[2:][:160], str(path.relative_to(ROOT))))
    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in open_items[:8]:
        best_score = 0.0
        best: tuple[str, str] | None = None
        for text, ref in corpus:
            sc = _overlap_score(item, text)
            if sc > best_score:
                best_score = sc
                best = (text, ref)
        if best and best_score >= 0.34:
            key = best[1]
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                {
                    "for_open": item[:120],
                    "wiki": best[1],
                    "snippet": best[0][:140],
                    "score": f"{best_score:.2f}",
                }
            )
        if len(hits) >= limit:
            break
    return hits


def _detect_repetition(
    open_items: list[str],
    done_pool: list[str],
    vault_texts: list[str],
    wiki_hits: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Flag open items that look already covered by done/vault/wiki."""
    flags: list[dict[str, Any]] = []
    for item in open_items[:10]:
        reasons: list[str] = []
        pointers: list[str] = []
        best_done = 0.0
        best_done_text = ""
        for d in done_pool:
            sc = _overlap_score(item, d)
            if sc > best_done:
                best_done = sc
                best_done_text = d
        if best_done >= 0.45:
            reasons.append(f"matches done work (score={best_done:.2f})")
            pointers.append(f"done: {best_done_text[:120]}")
        best_v = 0.0
        best_v_text = ""
        for v in vault_texts:
            sc = _overlap_score(item, v)
            if sc > best_v:
                best_v = sc
                best_v_text = v
        if best_v >= 0.40:
            reasons.append(f"vault already discusses this (score={best_v:.2f})")
            pointers.append(f"vault: {best_v_text[:120]}")
        for wh in wiki_hits:
            if wh.get("for_open") == item[:120] or _overlap_score(item, wh.get("for_open", "")) >= 0.5:
                reasons.append(f"wiki hit ({wh.get('score')})")
                pointers.append(f"wiki: {wh.get('wiki')} — {wh.get('snippet', '')[:80]}")
        if reasons:
            flags.append(
                {
                    "open_item": item,
                    "risk": "high" if best_done >= 0.55 or best_v >= 0.5 else "medium",
                    "reasons": reasons,
                    "pointers": pointers[:4],
                }
            )
    return flags


def _input_fingerprint() -> str:
    """Hash of inputs that change situation (skip rebuild when stable)."""
    parts: list[str] = []
    for rel in (
        "STATE.md",
        "VERSION",
        "reports/sessions/workstreams.yaml",
        "wiki/index.md",
        "wiki/open-questions.md",
    ):
        p = ROOT / rel
        if p.is_file():
            try:
                st = p.stat()
                parts.append(f"{rel}:{st.st_mtime_ns}:{st.st_size}")
            except OSError:
                parts.append(f"{rel}:missing")
    # latest resume + todo names + mtimes
    for pattern, base in (
        ("resume-*.md", SESSIONS),
        ("*_TODO.md", ROOT / "TODO"),
    ):
        if not base.is_dir():
            continue
        paths = sorted(base.glob(pattern), key=lambda x: x.name, reverse=True)[:3]
        for p in paths:
            try:
                st = p.stat()
                parts.append(f"{p.name}:{st.st_mtime_ns}:{st.st_size}")
            except OSError:
                pass
    if LEDGER.is_file():
        try:
            st = LEDGER.stat()
            # size + mtime only (not full file)
            parts.append(f"vault:{st.st_mtime_ns}:{st.st_size}")
        except OSError:
            pass
    code, br = _run(["git", "branch", "--show-current"])
    parts.append(f"branch:{br if code == 0 else '?'}")
    code, head = _run(["git", "rev-parse", "--short", "HEAD"])
    parts.append(f"head:{head if code == 0 else '?'}")
    blob = "|".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:20]


def load_cached_situation(*, max_age: int = CACHE_MAX_AGE) -> dict[str, Any] | None:
    """Return prior situation JSON if fingerprint matches and file is fresh."""
    if not SITUATION_JSON.is_file() or not SITUATION_FP.is_file():
        return None
    try:
        age = time.time() - SITUATION_JSON.stat().st_mtime
        if age > max_age:
            return None
        stored_fp = SITUATION_FP.read_text(encoding="utf-8").strip()
        if stored_fp != _input_fingerprint():
            return None
        data = json.loads(SITUATION_JSON.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("status") != "ok":
            return None
        data["cache_hit"] = True
        data["cache_age_s"] = int(age)
        # Prefer disk briefing_text if present
        if SITUATION_TXT.is_file() and not data.get("briefing_text"):
            data["briefing_text"] = SITUATION_TXT.read_text(encoding="utf-8")
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def build_situation() -> dict[str, Any]:
    rb = _resume_branch_kv()
    branch = rb.get("current") or _git_branch()
    remote_last = rb.get("remote_last") or ""
    on_tip = "yes" if remote_last and branch == remote_last else "no"
    resume_path = _latest_resume()
    resume = _parse_resume_card(resume_path)
    todo_path = _latest_todo()
    todo_open = _todo_open(todo_path)
    # Prefer resume open if present; merge unique with TODO
    open_items: list[str] = []
    for src in (resume.get("open") or [], todo_open):
        for it in src:
            if it not in open_items:
                open_items.append(it)
    open_items = open_items[:10]

    state = _state_snippets()
    done_pool = list(resume.get("done") or []) + list(state.get("done") or [])
    lessons = _vault_lessons(5)
    query = " | ".join(open_items[:5])[:280]
    precedents = _vault_precedents(query, limit=4) if open_items else []
    vault_texts = [l["text"] for l in lessons] + [
        str(p.get("judgment") or "") for p in precedents
    ]
    wiki_hits = _wiki_hits(open_items)
    repetition = _detect_repetition(open_items, done_pool, vault_texts, wiki_hits)

    where = {
        "branch": branch,
        "remote_last": remote_last or None,
        "on_remote_last": on_tip,
        "sync": rb.get("sync_status"),
        "switch_result": rb.get("switch_result"),
        "version": _template_version(),
        "behind_develop": _behind_develop(),
        "workstream_primary": _workstream_primary() or None,
        "resume_path": resume.get("path"),
        "todo": str(todo_path.relative_to(ROOT)) if todo_path else None,
        "date": date.today().isoformat(),
    }

    in_flight = {
        "open": open_items,
        "next": (resume.get("next") or [])[:5],
        "done_recent": (resume.get("done") or state.get("done") or [])[:5],
        "state_facts": state.get("facts") or [],
    }

    ask = None
    if repetition:
        ask = (
            "Repetition risk: some open items look already covered in vault/wiki/done work. "
            "Does prior work help, or leave it and carry on? "
            "[use prior | continue | re-scope]"
        )
    elif open_items:
        ask = (
            f"Situation loaded: {len(open_items)} open item(s) on "
            f"{branch} (team tip={remote_last or 'n/a'}). "
            "Confirm focus or pick next. [continue | fresh | switch focus]"
        )
    else:
        ask = (
            "No open TODO items found — confirm direction with operator before inventing work. "
            "[set direction | full standup]"
        )

    lines: list[str] = [
        "=== SESSION SITUATION (must understand before work) ===",
        (
            f"Where: branch={branch} remote_last={remote_last or 'none'} "
            f"on_tip={on_tip} sync={rb.get('sync_status') or '?'} "
            f"ver={where['version']} behind_develop={where['behind_develop']}"
        ),
    ]
    if where.get("workstream_primary"):
        lines.append(f"Workstream primary: {where['workstream_primary']}")
    if where.get("resume_path"):
        lines.append(f"Resume: {where['resume_path']}")
    if where.get("todo"):
        lines.append(f"TODO: {where['todo']}")

    lines.append("In flight (open):")
    if open_items:
        for i, it in enumerate(open_items[:6], 1):
            lines.append(f"  O{i}. {it[:140]}")
    else:
        lines.append("  (none)")

    if in_flight["done_recent"]:
        lines.append("Recently done (context):")
        for i, it in enumerate(in_flight["done_recent"][:4], 1):
            lines.append(f"  D{i}. {it[:120]}")

    if lessons:
        lines.append("Vault recent (do not re-plan blindly):")
        for i, les in enumerate(lessons[:3], 1):
            lines.append(f"  V{i}. [{les['type']}] {les['text'][:140]}")

    if precedents:
        lines.append("Vault precedents for open work:")
        for i, p in enumerate(precedents[:3], 1):
            lines.append(f"  P{i}. {str(p.get('judgment'))[:140]}")

    if wiki_hits:
        lines.append("Wiki related pages:")
        for i, w in enumerate(wiki_hits[:3], 1):
            lines.append(f"  W{i}. {w['wiki']}: {w['snippet'][:100]}")

    if repetition:
        lines.append(f"REPETITION RISK ({len(repetition)} item(s)) — remind user:")
        for i, r in enumerate(repetition[:5], 1):
            lines.append(f"  R{i}. [{r['risk']}] {r['open_item'][:100]}")
            for ptr in r.get("pointers") or []:
                lines.append(f"      → {ptr[:140]}")
        lines.append(
            "Ask: Does that prior work help, or leave it and carry on? "
            "[use prior | continue | re-scope]"
        )
    else:
        lines.append("Repetition: none strong — still cite vault/wiki before redoing similar work.")

    lines.append(f"ASK: {ask}")
    lines.append(
        "Agent rule: do not start implementation until situation is acknowledged; "
        "if repetition, wait for use prior | continue | re-scope."
    )
    lines.append("=== end situation ===")

    fp = _input_fingerprint()
    return {
        "status": "ok",
        "cache_hit": False,
        "fingerprint": fp,
        "where": where,
        "in_flight": in_flight,
        "vault_lessons": lessons,
        "vault_precedents": precedents,
        "wiki_hits": wiki_hits,
        "repetition": repetition,
        "repetition_count": len(repetition),
        "ask": ask,
        "agent_gate": "acknowledge_situation"
        + ("+repetition_choice" if repetition else ""),
        "briefing_lines": lines,
        "briefing_text": "\n".join(lines) + "\n",
    }


def write_situation(sit: dict[str, Any]) -> None:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    fp = sit.get("fingerprint") or _input_fingerprint()
    sit = {**sit, "fingerprint": fp}
    SITUATION_JSON.write_text(
        json.dumps(sit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    SITUATION_TXT.write_text(sit.get("briefing_text") or "", encoding="utf-8")
    SITUATION_FP.write_text(fp + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write reports/sessions/situation-latest.{json,txt}",
    )
    ap.add_argument(
        "--use-cache",
        action="store_true",
        help="Reuse situation-latest when input fingerprint matches (token + CPU save)",
    )
    ap.add_argument(
        "--max-age",
        type=int,
        default=CACHE_MAX_AGE,
        help=f"Cache max age seconds (default {CACHE_MAX_AGE})",
    )
    args = ap.parse_args()

    sit: dict[str, Any] | None = None
    if args.use_cache:
        sit = load_cached_situation(max_age=args.max_age)
    if sit is None:
        sit = build_situation()
        if args.write or args.use_cache:
            write_situation(sit)
    elif args.write:
        # refresh mtime path already present; keep disk as-is
        pass

    if args.json:
        # Drop bulky card-like fields already on disk when printing JSON to agents? keep full
        print(json.dumps(sit, indent=2, ensure_ascii=False))
    else:
        if sit.get("cache_hit"):
            sys.stdout.write(f"(situation cache hit age={sit.get('cache_age_s')}s)\n")
        sys.stdout.write(sit.get("briefing_text") or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
