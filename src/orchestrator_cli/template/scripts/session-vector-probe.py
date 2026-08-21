#!/usr/bin/env python3
"""Probe: would a small vector DB help session-start retrieval?

Compares three methods on vault lessons + wiki index vs open TODO/resume items:

  1. token_overlap  — current session-situation style (set Jaccard-ish)
  2. bow_cosine     — bag-of-words cosine (stdlib; no embedding API)
  3. oracle_keyword — upper bound: if any strong keyword from query is in doc

No new dependencies. Does **not** install Chroma/pgvector. Produces a report under
reports/research/ and JSON under reports/sessions/.

Usage:
  python3 scripts/session-vector-probe.py
  python3 scripts/session-vector-probe.py --json
  python3 scripts/session-vector-probe.py --write

Exit 0 always.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STOP = frozenset(
    "the and for with from that this when then into only after before using via "
    "run add use set get not any all new old if or to of in on a an is are be as "
    "at by it we do does done work item todo p0 p1 p2 p3".split()
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-_/]{2,}", text.lower())
    return [w for w in words if w not in STOP and not w.isdigit()]


def _overlap(a: str, b: str) -> float:
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


def _bow_cosine(a: str, b: str) -> float:
    ca, cb = Counter(_tokens(a)), Counter(_tokens(b))
    if not ca or not cb:
        return 0.0
    keys = set(ca) | set(cb)
    dot = sum(ca[k] * cb[k] for k in keys)
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _oracle(a: str, b: str) -> float:
    """1.0 if any high-signal query token length>=5 appears in doc."""
    sig = [t for t in _tokens(a) if len(t) >= 5][:12]
    bl = b.lower()
    hits = sum(1 for t in sig if t in bl)
    if not sig:
        return 0.0
    return hits / len(sig)


def load_corpus() -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    # Vault
    ledger = ROOT / "reports" / "vault" / "events.jsonl"
    if ledger.is_file():
        for i, line in enumerate(ledger.read_text(encoding="utf-8", errors="replace").splitlines()):
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            p = ev.get("payload") or {}
            text = ""
            for k in ("text", "summary", "lesson", "message", "branch"):
                if p.get(k):
                    text = str(p[k])
                    break
            if not text and p:
                text = json.dumps(p)[:300]
            if len(text) < 20:
                continue
            docs.append(
                {
                    "id": f"vault:{ev.get('type')}:{(ev.get('content_hash') or str(i))[:12]}",
                    "source": "vault",
                    "text": text[:800],
                }
            )
            if len([d for d in docs if d["source"] == "vault"]) >= 80:
                break
    # Wiki index rows
    wiki = ROOT / "wiki" / "index.md"
    if wiki.is_file():
        for line in _read(wiki).splitlines():
            m = re.search(r"\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.*)$", line)
            if m:
                docs.append(
                    {
                        "id": f"wiki:{m.group(2)}",
                        "source": "wiki",
                        "text": f"{m.group(1)} {m.group(3)}"[:500],
                    }
                )
    # Resume open/done
    sessions = ROOT / "reports" / "sessions"
    if sessions.is_dir():
        resumes = sorted(sessions.glob("resume-*.md"), reverse=True)[:3]
        for rpath in resumes:
            docs.append(
                {
                    "id": f"resume:{rpath.name}",
                    "source": "resume",
                    "text": _read(rpath)[:1500],
                }
            )
    # STATE done
    state = ROOT / "STATE.md"
    if state.is_file():
        docs.append({"id": "state:STATE.md", "source": "state", "text": _read(state)[:2500]})
    return docs


def load_queries() -> list[str]:
    qs: list[str] = []
    todo_dir = ROOT / "TODO"
    if todo_dir.is_dir():
        todos = sorted(todo_dir.glob("*_TODO.md"), reverse=True)[:2]
        for t in todos:
            for line in _read(t).splitlines():
                m = re.match(r"^\s*(?:[-*]|\d+\.)\s+\[\s*\]\s+(.+)$", line)
                if m:
                    qs.append(m.group(1).strip()[:160])
                if len(qs) >= 8:
                    break
    # Paraphrases to test semantic gap
    if qs:
        base = qs[0]
        qs.append(f"continue previous work on {base[:80]}")
        qs.append(f"did we already finish something like: {base[:60]}")
    # Fixed probes for template meta
    qs.extend(
        [
            "remote_last session start branch switch",
            "how does the knowledge vault compound learning work",
            "multi-workstream diamond recommend",
        ]
    )
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:12]


def topk(
    query: str, docs: list[dict[str, str]], score_fn, k: int = 3
) -> list[dict[str, Any]]:
    scored = []
    for d in docs:
        s = score_fn(query, d["text"])
        if s > 0:
            scored.append({"id": d["id"], "source": d["source"], "score": round(s, 4), "snip": d["text"][:100]})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def evaluate() -> dict[str, Any]:
    docs = load_corpus()
    queries = load_queries()
    methods = {
        "token_overlap": _overlap,
        "bow_cosine": _bow_cosine,
        "oracle_keyword": _oracle,
    }
    per_q: list[dict[str, Any]] = []
    # Compare agreement: how often bow top1 == overlap top1; oracle non-zero vs methods
    agree_bow_overlap = 0
    bow_beats_overlap = 0  # bow finds score>0.2 when overlap top is empty/weak
    n_q = 0
    for q in queries:
        n_q += 1
        row: dict[str, Any] = {"query": q, "methods": {}}
        tops: dict[str, list] = {}
        for name, fn in methods.items():
            tops[name] = topk(q, docs, fn, k=3)
            row["methods"][name] = tops[name]
        o1 = (tops["token_overlap"][0]["id"] if tops["token_overlap"] else None)
        b1 = (tops["bow_cosine"][0]["id"] if tops["bow_cosine"] else None)
        if o1 and b1 and o1 == b1:
            agree_bow_overlap += 1
        o_best = tops["token_overlap"][0]["score"] if tops["token_overlap"] else 0
        b_best = tops["bow_cosine"][0]["score"] if tops["bow_cosine"] else 0
        if b_best >= 0.25 and o_best < 0.2:
            bow_beats_overlap += 1
        per_q.append(row)

    corpus_n = len(docs)
    by_src: dict[str, int] = {}
    for d in docs:
        by_src[d["source"]] = by_src.get(d["source"], 0) + 1

    # Fit assessment (vector-database-expert rubric, tailored)
    score = 0
    signals: list[str] = []
    # Against
    if corpus_n < 1000:
        score -= 2
        signals.append(f"−2 corpus small (N={corpus_n} < 1k) — FTS/token enough")
    score -= 2
    signals.append("−2 orchestrator is CRUD+scripts+markdown; no product RAG surface")
    score -= 1
    signals.append("−1 prior decision: vector DB abandoned for orchestrator (resume history)")
    # For
    if bow_beats_overlap >= 2:
        score += 1
        signals.append(f"+1 bow_cosine beats token_overlap on {bow_beats_overlap} queries (mild semantic gap)")
    else:
        signals.append(f"+0 bow rarely beats overlap ({bow_beats_overlap}/{n_q}) — little vector upside")
    if by_src.get("vault", 0) > 30:
        score += 1
        signals.append(f"+1 vault has {by_src.get('vault')} events — eventual hybrid search maybe")

    if score >= 4:
        rec = "adopt"
    elif score >= 1:
        rec = "defer"
    else:
        rec = "reject"

    return {
        "date": date.today().isoformat(),
        "corpus_size": corpus_n,
        "corpus_by_source": by_src,
        "query_count": n_q,
        "agree_bow_overlap_top1": agree_bow_overlap,
        "agree_rate": round(agree_bow_overlap / max(1, n_q), 3),
        "bow_beats_overlap_count": bow_beats_overlap,
        "recommendation": rec,
        "score": score,
        "signals": signals,
        "alternatives": [
            "Keep token_overlap + bow_cosine in session-situation-brief (stdlib)",
            "Vault find_precedents + session-vault-todo-query (already)",
            "Optional later: sqlite FTS5 over events.jsonl if vault > few k events",
            "Do not add Chroma/pgvector/embedding API for session-start alone",
        ],
        "when_revisit": [
            "Vault events > ~5k and keyword search fails on paraphrases",
            "Multi-app shared knowledge RAG product requirement",
            "User-facing semantic search over docs (not agent spin-up)",
        ],
        "per_query": per_q[:6],  # sample for report size
    }


def render_md(ev: dict[str, Any]) -> str:
    lines = [
        f"# Vector / session retrieval probe — {ev['date']}",
        "",
        "## Recommendation",
        "",
        f"**{ev['recommendation'].upper()}** (score={ev['score']})",
        "",
        "### Signals",
        "",
    ]
    for s in ev["signals"]:
        lines.append(f"- {s}")
    lines += [
        "",
        "## Corpus",
        "",
        f"- Size: **{ev['corpus_size']}** docs",
        f"- By source: `{ev['corpus_by_source']}`",
        f"- Queries: {ev['query_count']}",
        f"- BOW vs token_overlap top-1 agree rate: **{ev['agree_rate']}**",
        f"- BOW beats weak overlap: **{ev['bow_beats_overlap_count']}** queries",
        "",
        "## Interpretation",
        "",
        "A dedicated vector DB (Chroma/Qdrant/pgvector + embeddings) adds ops cost "
        "(model version, reindex, PII policy) for **session-start**. This probe shows "
        "stdlib BOW already tracks token-overlap closely; embeddings would only help "
        "when paraphrase gaps dominate — not the case on this small meta-repo.",
        "",
        "## Alternatives (token-efficient)",
        "",
    ]
    for a in ev["alternatives"]:
        lines.append(f"- {a}")
    lines += ["", "## Revisit when", ""]
    for w in ev["when_revisit"]:
        lines.append(f"- {w}")
    lines += [
        "",
        "## Sample query tops (truncated)",
        "",
    ]
    for row in ev.get("per_query") or []:
        lines.append(f"### Q: {row['query'][:100]}")
        for m, hits in (row.get("methods") or {}).items():
            top = hits[0] if hits else {"id": "—", "score": 0}
            lines.append(f"- `{m}`: {top.get('id')} ({top.get('score')})")
        lines.append("")
    lines.append("_Generated by `scripts/session-vector-probe.py` (no embedding deps)._")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", action="store_true", help="Write report + sessions JSON")
    args = ap.parse_args()

    ev = evaluate()
    md = render_md(ev)

    if args.write:
        research = ROOT / "reports" / "research"
        research.mkdir(parents=True, exist_ok=True)
        out_md = research / f"vector-session-probe-{ev['date']}.md"
        out_md.write_text(md, encoding="utf-8")
        sess = ROOT / "reports" / "sessions"
        sess.mkdir(parents=True, exist_ok=True)
        (sess / "vector-probe-latest.json").write_text(
            json.dumps(ev, indent=2) + "\n", encoding="utf-8"
        )
        ev["report_path"] = str(out_md.relative_to(ROOT))

    if args.json:
        print(json.dumps(ev, indent=2))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
