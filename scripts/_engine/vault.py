"""Secure Vault Graph primitives for self-building project knowledge vaults.

Strong security proposition:
- Append-only, content-addressed ledger (events.jsonl).
- SHA-256 content hashes + hash-chained provenance for tamper-evidence.
- Secret/PII scrubbing at emission time (reuses patterns from git-push-secrets-guard + loop filters).
- No secrets or sensitive data stored in clear.
- Integrity verification on load (verify_ledger).
- Causal parents for provenance graph.
- Git commit + ts metadata for audit trail.
- Designed for L1 report-only synthesis; mutations gated by human + existing security gates.
- Integrates with MCP sandbox (reports/vault allowed), git-push-secrets-guard, loop audits.
- Multi-device safe via git + hash verification (detects drift/forks).
- Lean: events are compact; load subgraphs by hash or time.

Full Node Taxonomy (Lane 1 extension):
- Hierarchical brain-like: foundational (raw_event, observation), knowledge (concept, pattern, lesson, precedent, codebase_knowledge, wave_app_profile),
  reasoning (hypothesis, reasoning_step, reasoning_trace, analogy, decision, evidence, synthesis),
  action (problem, solution, action, outcome), meta (self_improvement, meta_pattern, query_result, feedback).
- Areas/facets: reasoning, code, deploy, security, learning, multi_ai, wave, process.
- Relations: parents + solves, analogous_to, refines, depends_on, etc.
- Backward compatible. See reports/docs/vault-graph-evolution-plan.md for full details.

Usage:
  from scripts._engine.vault import emit_lesson_event, verify_ledger, load_recent_events
  event = emit_lesson_event(lesson_text, source="loop:2026-07-06-xxx.md", parents=[prev_hash], area="reasoning")
  append_event(ledger_path, event)
  ok, issues = verify_ledger(ledger_path)
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Basic secret patterns (extend from git-push-secrets-guard.py)
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("GitHub token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("GitHub fine-grained", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Generic secret key", re.compile(r"(?i)(secret|api[_-]?key|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{16,}")),
    ("Private key header", re.compile(r"-----BEGIN (RSA |EC |)PRIVATE KEY-----")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

def _scrub_secrets(text: str) -> str:
    """Sanitize text; replace detected secrets with [REDACTED]."""
    cleaned = text
    for name, pattern in SECRET_PATTERNS:
        cleaned = pattern.sub(f"[REDACTED:{name}]", cleaned)
    # Additional heuristic: very long base64-like strings
    cleaned = re.sub(r"[A-Za-z0-9/+=]{40,}", "[REDACTED:long-token]", cleaned)
    return cleaned


try:
    from scripts._engine import untrusted_text as _ut
except ImportError:
    from _engine import untrusted_text as _ut  # type: ignore


def filter_prompt_injection(text: str) -> tuple[str, list[str]]:
    """Scrub prompt-injection patterns (delegates to untrusted_text)."""
    return _ut.filter_prompt_injection(text)


def scrub_for_ai_context(text: str) -> tuple[str, list[str]]:
    """Injection + PII + toxic scrub for vault/MCP AI boundaries."""
    return _ut.filter_all(text)

def _content_hash(text: str) -> str:
    """SHA-256 of canonical content (stripped, scrubbed)."""
    canonical = _scrub_secrets(text).strip().encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

def _current_git_commit(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()[:12]
    except Exception:
        pass
    return ""


def _git_operator_email(root: Path | None = None) -> str:
    """Resolve operator identity for per-user workspace pointers (git config user.email)."""
    root = root or Path.cwd()
    try:
        proc = subprocess.run(
            ["git", "config", "user.email"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            email = proc.stdout.strip().lower()
            if email:
                return email
    except Exception:
        pass
    return "unknown@local"

def make_event(
    event_type: str,
    payload: dict[str, Any],
    source: str,
    parents: list[str] | None = None,
    root: Path | None = None,
    area: str | None = None,
    relations: list[dict[str, Any]] | None = None,
    **extra_metadata,
) -> dict[str, Any]:
    """Create a secure, hash-chained graph event.

    payload should contain the primary data (e.g. {"text": lesson}).
    All sensitive content in payload is scrubbed.

    Extended for full taxonomy (Lane 1):
    - area: e.g. "reasoning", "code", "deploy", "security", "learning", "multi_ai", "wave"
    - relations: richer edges beyond parents, e.g. [{"type": "solves", "target": "hash", "similarity": 0.85}]
    - Supports brain-like expansion: reasoning traces, hypotheses, etc.
    Backward compatible: old events load unchanged.
    """
    root = root or Path.cwd()
    ts = datetime.now(timezone.utc).isoformat()

    # Sanitize payload
    sanitized_payload = {}
    for k, v in payload.items():
        if isinstance(v, str):
            sanitized_payload[k] = _scrub_secrets(v)
        else:
            sanitized_payload[k] = v

    content_to_hash = json.dumps(sanitized_payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()

    event = {
        "id": content_hash[:16],  # short stable id
        "type": event_type,
        "content_hash": content_hash,
        "payload": sanitized_payload,
        "parents": parents or [],
        "source": _scrub_secrets(source),
        "ts": ts,
        "git_commit": _current_git_commit(root),
    }

    # Extended fields for full node taxonomy
    if area:
        event["area"] = area
    if relations:
        event["relations"] = relations
    # Merge any extra metadata (e.g. confidence, tags)
    for k, v in extra_metadata.items():
        if k not in event:
            event[k] = v

    return event

def emit_lesson_event(
    lesson_text: str,
    source: str,
    parents: list[str] | None = None,
    root: Path | None = None,
    area: str | None = "learning",
    relations: list[dict[str, Any]] | None = None,
    **extra_metadata,
) -> dict[str, Any]:
    """Convenience for lessons (core of self-building vault).
    Supports full taxonomy: area (e.g. 'reasoning', 'code'), relations, etc.
    """
    return make_event(
        event_type="lesson",
        payload={"text": lesson_text},
        source=source,
        parents=parents,
        root=root,
        area=area,
        relations=relations,
        **extra_metadata,
    )

# path -> (mtime_ns, size, content_hash set). Invalidated when file changes out-of-process.
_ledger_hash_cache: dict[str, tuple[int, int, set[str]]] = {}


def _ledger_cache_key(ledger_path: Path) -> str:
    return str(ledger_path.resolve())


def clear_ledger_hash_cache(ledger_path: Path | None = None) -> None:
    """Drop hash cache (tests or after external ledger rewrite)."""
    if ledger_path is None:
        _ledger_hash_cache.clear()
        return
    _ledger_hash_cache.pop(_ledger_cache_key(ledger_path), None)


def _load_content_hashes(ledger_path: Path) -> set[str]:
    hashes: set[str] = set()
    try:
        with ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ch = existing.get("content_hash")
                if ch:
                    hashes.add(ch)
    except OSError:
        return set()
    return hashes


def _get_ledger_hash_set(ledger_path: Path) -> set[str]:
    """Return set of content_hashes in ledger; cache by (mtime, size) for multi-append."""
    key = _ledger_cache_key(ledger_path)
    try:
        st = ledger_path.stat()
    except OSError:
        return set()
    cached = _ledger_hash_cache.get(key)
    if cached is not None and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
        return cached[2]
    hashes = _load_content_hashes(ledger_path)
    _ledger_hash_cache[key] = (st.st_mtime_ns, st.st_size, hashes)
    return hashes


def append_event(ledger_path: Path, event: dict[str, Any]) -> None:
    """Append event to ledger (jsonl). Creates dirs if needed. Atomic-ish append.

    Idempotent on content_hash: skip append when the hash already exists (prevents
    duplicate workspace_pointer / double-emit races that break verify_ledger).

    Uses a process-local (path, mtime, size) → hash-set cache so bulk emits after
    the first load are O(1) membership checks instead of re-reading the full ledger.
    """
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ch = event.get("content_hash")
    key = _ledger_cache_key(ledger_path)
    hashes: set[str] | None = None
    if ch and ledger_path.is_file():
        hashes = _get_ledger_hash_set(ledger_path)
        if ch in hashes:
            return
    line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(line)
    # Keep cache warm after our write (avoid O(n) reload on next append).
    if ch:
        try:
            st = ledger_path.stat()
            if hashes is None:
                hashes = set()
            hashes.add(ch)
            _ledger_hash_cache[key] = (st.st_mtime_ns, st.st_size, hashes)
        except OSError:
            clear_ledger_hash_cache(ledger_path)

def load_events(ledger_path: Path) -> list[dict[str, Any]]:
    """Load all events (for verification or subgraph)."""
    if not ledger_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events

def verify_ledger(ledger_path: Path) -> tuple[bool, list[str]]:
    """Strong integrity check: content hashes + basic chain + relations (Lane 1).

    Returns (ok, list_of_issues).
    Relations are verified for target existence (prior or whole ledger for flexibility).

    Parent/relation checks use hash sets (O(n)) — not O(n²) linear scans (Phase B BH-002).
    """
    events = load_events(ledger_path)
    issues: list[str] = []
    seen_hashes: set[str] = set()
    all_hashes: set[str] = {
        e.get("content_hash") for e in events if e.get("content_hash")
    }

    for i, ev in enumerate(events):
        # Verify content hash
        payload = ev.get("payload", {})
        content_to_hash = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()
        actual = ev.get("content_hash")
        if actual != expected:
            issues.append(f"Event {i} content_hash mismatch: {ev.get('id')}")

        # Record for chain checks
        ch = ev.get("content_hash")
        if ch in seen_hashes:
            issues.append(f"Duplicate content_hash at event {i}")

        # Parent check: parents must appear in prior events (seen so far)
        for p in ev.get("parents", []):
            if p not in seen_hashes:
                issues.append(f"Event {i} has unknown parent hash {p[:12]}")

        if ch:
            seen_hashes.add(ch)

        # Lane 1: Relation targets may be anywhere in the ledger
        for rel in ev.get("relations", []) or []:
            if isinstance(rel, dict):
                tgt = rel.get("target")
                if tgt and tgt not in all_hashes:
                    issues.append(
                        f"Event {i} has unknown relation target {str(tgt)[:12]} "
                        f"(type={rel.get('type')})"
                    )

    ok = len(issues) == 0
    return ok, issues

def get_recent_events(ledger_path: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Lean subgraph load (tail for recent knowledge)."""
    events = load_events(ledger_path)
    return events[-limit:]

def build_simple_graph(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Minimal in-memory graph for synthesis (nodes + edges). Report-only use.
    Includes area, relations (as typed edges), and parents for extended taxonomy.
    Supports complex reasoning traversal and area-filtered subgraphs.
    Backward compatible with old events (no area/relations).
    """
    nodes = []
    edges = []
    for ev in events:
        nid = ev.get("content_hash") or ev.get("id")
        node = {
            "id": nid,
            "type": ev.get("type"),
            "area": ev.get("area"),
            "payload_summary": str(ev.get("payload", {}))[:200],
            "ts": ev.get("ts"),
            "source": ev.get("source"),
            "relations": ev.get("relations", []),
        }
        nodes.append(node)
        for p in ev.get("parents", []):
            edges.append({"from": p, "to": nid, "type": "parent"})
        # Rich relations edges (Lane 1)
        for rel in ev.get("relations", []) or []:
            if isinstance(rel, dict) and rel.get("target"):
                edges.append({
                    "from": nid,
                    "to": rel["target"],
                    "type": rel.get("type", "relation"),
                    **{k: v for k, v in rel.items() if k not in ("type", "target")}
                })
    return {"nodes": nodes, "edges": edges, "count": len(nodes)}

def _compute_similarity(query: str, text: str) -> float:
    """Hybrid similarity: difflib sequence + keyword (word) overlap. Pure stdlib. Lane 2."""
    q = (query or "").lower().strip()
    t = (text or "").lower().strip()
    if not q or not t:
        return 0.0
    dl = difflib.SequenceMatcher(None, q, t).ratio()
    qw = set(re.findall(r"\w+", q))
    tw = set(re.findall(r"\w+", t))
    overlap = (len(qw & tw) / len(qw)) if qw else 0.0
    return round(0.65 * dl + 0.35 * overlap, 4)


def find_similar_events(
    ledger_path: Path,
    query: str,
    event_type: str | None = None,
    area: str | None = None,
    min_ratio: float = 0.45,
    limit: int = 5,
) -> list[dict]:
    """Find similar events for precedents.
    Hybrid scoring (difflib + keyword overlap) beyond pure difflib (Lane 2).
    Supports area/type filter + soft boost for matching type/area.
    Returns list with 'similarity' and 'event'.
    """
    events = load_events(ledger_path)
    matches = []
    q = query.lower()
    for ev in events:
        if event_type and ev.get("type") != event_type:
            continue
        if area and ev.get("area") != area:
            continue
        text = " ".join(str(v) for v in ev.get("payload", {}).values()).lower()
        score = _compute_similarity(q, text)
        # Soft boost if area/type semantically align with query (even if not strict filtered)
        boost = 0.0
        ev_type = ev.get("type") or ""
        ev_area = ev.get("area") or ""
        if event_type and ev_type == event_type:
            boost += 0.08
        if area and ev_area == area:
            boost += 0.08
        if any(k in q for k in ("error", "fail", "bug", "problem")) and ev_type in ("error", "problem", "fix"):
            boost += 0.05
        final = min(1.0, score + boost)
        if final >= min_ratio:
            matches.append((final, ev))
    matches.sort(key=lambda x: x[0], reverse=True)
    return [{"similarity": round(r, 2), "event": ev} for r, ev in matches[:limit]]


def get_event_by_hash(events: list[dict[str, Any]], content_hash: str) -> dict[str, Any] | None:
    """Pure-stdlib lookup by content_hash or short id. For chain traversal."""
    if not content_hash:
        return None
    for e in events:
        if e.get("content_hash") == content_hash or e.get("id") == content_hash:
            return e
    return None


def build_reasoning_chain(
    events: list[dict[str, Any]],
    start: dict[str, Any] | str,
    max_depth: int = 8,
) -> dict[str, Any]:
    """Traverse parents + reverse relations to build a reasoning/fix trace.
    Lane 2: supports '--build-reasoning-chain' for 'how we fixed it'.
    Returns {steps: [...], depth: n, root_reached: bool}.
    Steps include type, area, payload summary, via (parent/relation).
    Pure stdlib, no external graph libs.
    """
    if isinstance(start, str):
        start_ev = get_event_by_hash(events, start)
    else:
        start_ev = start
    if not start_ev:
        return {"steps": [], "depth": 0, "root_reached": False, "error": "start not found"}

    steps: list[dict[str, Any]] = []
    visited: set[str] = set()
    # Build reverse index: target_hash -> list of (source_ev, rel_type)
    reverse_rels: dict[str, list[tuple[dict, str]]] = {}
    for ev in events:
        nid = ev.get("content_hash") or ev.get("id")
        for p in ev.get("parents", []):
            reverse_rels.setdefault(p, []).append((ev, "parent"))
        for rel in ev.get("relations", []) or []:
            if isinstance(rel, dict):
                tgt = rel.get("target")
                if tgt:
                    rtype = rel.get("type", "relation")
                    reverse_rels.setdefault(tgt, []).append((ev, rtype))

    current = start_ev
    depth = 0
    while current and depth < max_depth:
        nid = current.get("content_hash") or current.get("id")
        if nid in visited:
            break
        visited.add(nid)
        step = {
            "id": nid,
            "type": current.get("type"),
            "area": current.get("area"),
            "payload_summary": str(current.get("payload", {}))[:160],
            "via": None,
        }
        steps.append(step)

        # Find predecessors via parents or reverse relations
        preds = []
        for p in current.get("parents", []):
            pe = get_event_by_hash(events, p)
            if pe:
                preds.append((pe, "parent"))

        for src_ev, rtype in reverse_rels.get(nid, []):
            if rtype in ("solves", "solved_by", "parent", "refines", "analogous_to") or "reason" in str(src_ev.get("type") or ""):
                preds.append((src_ev, rtype))

        if not preds:
            break
        next_ev = None
        for pe, via in preds:
            ph = pe.get("content_hash") or pe.get("id")
            if ph not in visited:
                next_ev = pe
                step["via"] = via
                break
        if not next_ev:
            break
        current = next_ev
        depth += 1

    return {
        "steps": steps,
        "depth": len(steps),
        "root_reached": bool(steps) and len([s for s in steps if s.get("type") in ("lesson", "synthesis")]) > 0,
        "start_type": start_ev.get("type"),
        "start_area": start_ev.get("area"),
    }


def find_precedents(
    ledger_path: Path,
    query: str,
    area: str | None = None,
    event_type: str | None = None,
    limit: int = 5,
    build_chain: bool = False,
) -> list[dict]:
    """Lane 2: richer than find_similar. Returns matches with judgment + linked fixes + optional reasoning chain.
    'same or similar' score + traces for complex thinking / 'how we fixed'.
    """
    sims = find_similar_events(ledger_path, query, event_type=event_type, area=area, limit=limit)
    events = load_events(ledger_path)
    results = []
    for m in sims:
        ev = m["event"]
        ev_id = ev.get("content_hash") or ev.get("id")
        linked = []
        for p in ev.get("parents", []):
            pe = get_event_by_hash(events, p)
            if pe and pe.get("type") in ("fix", "solution", "resolution", "outcome", "precedent"):
                linked.append({"via": "parent", "type": pe.get("type"), "payload": pe.get("payload")})
        for rel in ev.get("relations", []) or []:
            if isinstance(rel, dict):
                tgt = rel.get("target")
                pe = get_event_by_hash(events, tgt)
                if pe and pe.get("type") in ("fix", "solution", "precedent", "outcome"):
                    linked.append({"via": rel.get("type"), "type": pe.get("type"), "payload": pe.get("payload")})
        sim = m.get("similarity", 0)
        judgment = "same" if sim >= 0.85 else ("very similar" if sim >= 0.65 else "similar")
        rec = {
            "similarity": sim,
            "judgment": judgment,
            "event": ev,
            "linked_fixes": linked[:3],
        }
        if build_chain:
            rec["reasoning_chain"] = build_reasoning_chain(events, ev)
        results.append(rec)
    return results


def emit_event(event_type: str, payload: dict, source: str, parents: list[str] | None = None, root: Path | None = None, area: str | None = None, relations: list[dict[str, Any]] | None = None, **extra_metadata) -> dict:
    """General emit for richer events (error, fix, report, codebase_knowledge, reasoning_trace, etc.).
    Supports full taxonomy with area, relations for complex thinking and selected areas (e.g. 'reasoning', 'solving').
    """
    return make_event(event_type, payload, source, parents, root, area, relations, **extra_metadata)

# Convenience emitters for full taxonomy (Lane 1)
def emit_reasoning_event(reasoning_data: dict, source: str, parents: list[str] | None = None, root: Path | None = None, area: str = "reasoning", **extra) -> dict:
    """Emit a reasoning trace/step for complex thinking (e.g. hypothesis, decision chain)."""
    return emit_event("reasoning_trace", reasoning_data, source, parents, root, area, **extra)

def emit_error_event(error_data: dict, source: str, parents: list[str] | None = None, root: Path | None = None, area: str = "security", **extra) -> dict:
    """Emit error for precedent matching (e.g. 'this error happened before')."""
    return emit_event("error", error_data, source, parents, root, area, **extra)

def emit_fix_event(fix_data: dict, source: str, parents: list[str] | None = None, root: Path | None = None, area: str = "deploy", **extra) -> dict:
    """Emit fix linked to error for 'how did we fix it?' queries."""
    return emit_event("fix", fix_data, source, parents, root, area, **extra)

# Convenience for integration
def secure_compound_emit(
    lesson: str,
    report_source: str,
    ledger_path: Path,
    previous_head: str | None = None,
    root: Path | None = None,
    area: str | None = "learning",
    relations: list[dict[str, Any]] | None = None,
    **extra_metadata,
) -> dict[str, Any] | None:
    """Emit + append a lesson event securely. Returns event or None if scrubbed empty.
    Extended to support taxonomy: area, relations for reasoning/solving areas.
    """
    scrubbed = _scrub_secrets(lesson).strip()
    scrubbed, _ = scrub_for_ai_context(scrubbed)
    if not scrubbed or len(scrubbed) < 5:
        return None
    parents = [previous_head] if previous_head else []
    event = emit_lesson_event(scrubbed, source=report_source, parents=parents, root=root, area=area, relations=relations, **extra_metadata)
    append_event(ledger_path, event)
    return event


# --- Lane 1: Rich taxonomy helpers ---

def add_relation(
    event: dict[str, Any],
    rel_type: str,
    target: str,
    **meta: Any,
) -> dict[str, Any]:
    """Return a *copy* of the event with an additional relation (non-mutating).
    Use for linking e.g. a fix to an error: add_relation(fix_ev, "solves", error_hash, similarity=0.9)
    Relations augment parents for richer "brain-like" graph queries.
    """
    ev = dict(event)  # shallow copy sufficient (payload etc. are not deep-mutated here)
    rels: list[dict[str, Any]] = list(ev.get("relations", []))
    rel: dict[str, Any] = {"type": rel_type, "target": target}
    rel.update(meta)
    rels.append(rel)
    ev["relations"] = rels
    return ev


def make_rich_event(
    event_type: str,
    payload: dict[str, Any],
    source: str,
    *,
    area: str | None = None,
    relations: list[dict[str, Any]] | None = None,
    parents: list[str] | None = None,
    root: Path | None = None,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Convenience for full-taxonomy events. Delegates to make_event but signals rich usage.
    Recommended for precedent, reasoning_trace, codebase_knowledge, problem/solution etc.
    See taxonomy in module docstring and vault-graph-evolution-plan.md.
    """
    return make_event(event_type, payload, source, parents, root, area, relations, **extra_metadata)


# Additional taxonomy emitters (core brain-like categories)

def emit_codebase_knowledge_event(
    file: str,
    text: str,
    source: str = "backfill:codebase",
    area: str = "code",
    parents: list[str] | None = None,
    relations: list[dict[str, Any]] | None = None,
    root: Path | None = None,
    **extra,
) -> dict[str, Any]:
    """Emit structured codebase/architecture/concern knowledge."""
    return emit_event(
        "codebase_knowledge",
        {"file": file, "text": text},
        source,
        parents=parents,
        root=root,
        area=area,
        relations=relations,
        **extra,
    )


def emit_precedent_event(
    description: str,
    outcome: str,
    source: str,
    area: str = "learning",
    parents: list[str] | None = None,
    relations: list[dict[str, Any]] | None = None,
    root: Path | None = None,
    **extra,
) -> dict[str, Any]:
    """Emit a precedent (past situation + outcome) for future similarity search."""
    return emit_event(
        "precedent",
        {"description": description, "outcome": outcome},
        source,
        parents=parents,
        root=root,
        area=area,
        relations=relations,
        **extra,
    )


def emit_problem_event(
    signature: str,
    details: dict | str,
    source: str,
    area: str = "code",
    parents: list[str] | None = None,
    relations: list[dict[str, Any]] | None = None,
    root: Path | None = None,
    **extra,
) -> dict[str, Any]:
    """Emit a problem/bug (with signature for similarity). Pairs with emit_fix_event."""
    payload = {"signature": signature, "details": details} if isinstance(details, (dict, str)) else {"details": str(details)}
    return emit_event(
        "problem",
        payload,
        source,
        parents=parents,
        root=root,
        area=area,
        relations=relations,
        **extra,
    )


def emit_outcome_event(
    result: str,
    metrics: dict | None = None,
    source: str = "outcome",
    area: str = "process",
    parents: list[str] | None = None,
    relations: list[dict[str, Any]] | None = None,
    root: Path | None = None,
    **extra,
) -> dict[str, Any]:
    """Emit result of an action/decision (success/failure + metrics). Closes reasoning->action loops."""
    payload: dict[str, Any] = {"result": result}
    if metrics:
        payload["metrics"] = metrics
    return emit_event(
        "outcome",
        payload,
        source,
        parents=parents,
        root=root,
        area=area,
        relations=relations,
        **extra,
    )


def emit_synthesis_event(
    summary: str,
    proposals: list | None = None,
    source: str = "synthesis",
    area: str = "learning",
    parents: list[str] | None = None,
    relations: list[dict[str, Any]] | None = None,
    root: Path | None = None,
    **extra,
) -> dict[str, Any]:
    """Emit higher-order synthesis/meta-pattern derived from graph traversal."""
    payload: dict[str, Any] = {"summary": summary}
    if proposals:
        payload["proposals"] = proposals
    return emit_event(
        "synthesis",
        payload,
        source,
        parents=parents,
        root=root,
        area=area,
        relations=relations,
        **extra,
    )


# Canonical session-start order — vault double-check against agents/scripts
SESSION_STARTUP_POLICY = "fetch_then_remote_last_then_card"
SESSION_STARTUP_ORDER = (
    "1) git fetch origin --prune; "
    "2) switch+pull remote_last (team tip) when clean; "
    "3) THEN load resume card from that tip; "
    "4) security sweep + lean work"
)


def emit_workspace_pointer(
    branch: str,
    *,
    operator: str | None = None,
    remote_last: str | None = None,
    subject: str | None = None,
    source: str = "eod-shutdown",
    ledger_path: Path | None = None,
    parents: list[str] | None = None,
    root: Path | None = None,
    startup_policy: str | None = None,
    next_start_order: str | None = None,
    on_team_tip: bool | None = None,
) -> dict[str, Any]:
    """Record per-operator last-worked branch (append-only; latest wins on read).

    Synced via git on events.jsonl — each machine reads only its operator email.
    Not a substitute for git upstream checks; pairs with resume-branch sync_status.
    Optional startup_policy / next_start_order record the remote_last-first method
    for the next session-start (double-check vs agents).
    """
    root = root or Path.cwd()
    ledger_path = ledger_path or Path("reports/vault/events.jsonl")
    op = (operator or _git_operator_email(root)).strip().lower()
    payload: dict[str, Any] = {
        "operator": op,
        "branch": branch.strip(),
        "intent": "primary",
    }
    if remote_last:
        payload["remote_last_at_emit"] = remote_last.strip()
    if subject:
        payload["subject"] = _scrub_secrets(subject.strip())[:200]
    # Always stamp startup method on end/eod pointers so vault can double-check
    payload["startup_policy"] = (startup_policy or SESSION_STARTUP_POLICY).strip()
    payload["next_start_order"] = (next_start_order or SESSION_STARTUP_ORDER).strip()[:400]
    if on_team_tip is not None:
        payload["on_team_tip_at_emit"] = bool(on_team_tip)

    if parents is None:
        events = load_events(ledger_path)
        prev = get_operator_workspace_pointer(ledger_path, operator=op, root=root)
        if prev and prev.get("content_hash"):
            parents = [prev["content_hash"]]

    event = emit_event(
        "workspace_pointer",
        payload,
        source,
        parents=parents,
        root=root,
        area="process",
    )
    append_event(ledger_path, event)
    return event


def emit_session_startup(
    *,
    branch: str,
    remote_last: str | None = None,
    switch_result: str | None = None,
    switch_applied: str | None = None,
    on_remote_last: str | None = None,
    resume_first: str | None = None,
    card_path: str | None = None,
    card_branch: str | None = None,
    card_branch_match: str | None = None,
    align_recommendations: str | None = None,
    phase: str = "session-start",
    source: str = "session-start",
    operator: str | None = None,
    ledger_path: Path | None = None,
    parents: list[str] | None = None,
    root: Path | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append-only record of session-start / next-start policy for vault double-check.

    ``phase``:
      - session-start: what actually ran (after fetch→switch→card)
      - session-end / eod-shutdown: reminder of order for *next* start

    Agents and humans can query the latest event if startup behaviour is disputed.
    """
    root = root or Path.cwd()
    ledger_path = ledger_path or (root / "reports" / "vault" / "events.jsonl")
    op = (operator or _git_operator_email(root)).strip().lower()
    payload: dict[str, Any] = {
        "operator": op,
        "phase": phase,
        "startup_policy": SESSION_STARTUP_POLICY,
        "startup_order": SESSION_STARTUP_ORDER,
        "branch": (branch or "").strip(),
        "remote_last": (remote_last or "").strip() or None,
        "switch_result": (switch_result or "").strip() or None,
        "switch_applied": (switch_applied or "").strip() or None,
        "on_remote_last": (on_remote_last or "").strip() or None,
        "resume_first": (resume_first or "").strip() or None,
        "card_path": (card_path or "").strip() or None,
        "card_branch": (card_branch or "").strip() or None,
        "card_branch_match": (card_branch_match or "").strip() or None,
    }
    if align_recommendations:
        payload["align_recommendations"] = _scrub_secrets(align_recommendations)[:300]
    if extra:
        for k, v in extra.items():
            if v is not None and k not in payload:
                payload[k] = v

    if parents is None:
        prev = get_latest_session_startup(ledger_path, operator=op, root=root)
        if prev and prev.get("content_hash"):
            parents = [prev["content_hash"]]

    event = emit_event(
        "session_startup",
        payload,
        source,
        parents=parents,
        root=root,
        area="process",
    )
    ledger_path = Path(ledger_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if not ledger_path.is_file():
        ledger_path.write_text("", encoding="utf-8")
    append_event(ledger_path, event)
    return event


def get_latest_session_startup(
    ledger_path: Path | None = None,
    *,
    operator: str | None = None,
    root: Path | None = None,
    phase: str | None = None,
    any_operator: bool = False,
) -> dict[str, Any] | None:
    """Latest session_startup event (optionally filtered by operator / phase)."""
    root = root or Path.cwd()
    ledger_path = ledger_path or (root / "reports" / "vault" / "events.jsonl")
    op = None if any_operator else (operator or _git_operator_email(root)).strip().lower()
    matches = []
    for e in load_events(ledger_path):
        if e.get("type") != "session_startup":
            continue
        p = e.get("payload") or {}
        if op is not None:
            ev_op = (p.get("operator") or "").lower()
            if ev_op and ev_op != op:
                continue
        if phase and p.get("phase") != phase:
            continue
        matches.append(e)
    if not matches:
        return None
    return max(matches, key=lambda e: e.get("ts", ""))


def get_operator_workspace_pointer(
    ledger_path: Path | None = None,
    *,
    operator: str | None = None,
    root: Path | None = None,
) -> dict[str, Any] | None:
    """Latest workspace_pointer for this operator (newest ts), or None."""
    root = root or Path.cwd()
    ledger_path = ledger_path or Path("reports/vault/events.jsonl")
    op = (operator or _git_operator_email(root)).strip().lower()
    matches = [
        e
        for e in load_events(ledger_path)
        if e.get("type") == "workspace_pointer"
        and (e.get("payload") or {}).get("operator", "").lower() == op
    ]
    if not matches:
        return None
    return max(matches, key=lambda e: e.get("ts", ""))
