"""LLM + heuristic backends for always-on memory (Ollama catalog models + fallback)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .memory_models import pick_model_for_role
from .ollama_detect import detect_api, resolve_ollama_host

try:
    from . import untrusted_text as _ut
except ImportError:  # pragma: no cover
    _ut = None  # type: ignore


def scrub_text(text: str) -> str:
    if _ut is not None:
        cleaned, _ = _ut.filter_all(text)
        return cleaned
    return text


def _ollama_generate(model: str, prompt: str, *, timeout: float = 120.0) -> str:
    host = resolve_ollama_host()
    url = f"{host}/api/generate"
    body = json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "format": "json"}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return str(payload.get("response") or "")


def _extract_json_obj(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def heuristic_ingest(text: str, source: str = "") -> dict[str, Any]:
    """No-LLM structured extract — always available."""
    cleaned = scrub_text(text).strip()
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    # Prefer multi-line snapshot for seeds (VERSION + branch + TODO open items)
    if len(lines) >= 2:
        summary = " | ".join(lines[:4])[:400]
    else:
        summary = (lines[0] if lines else cleaned)[:240]
    # crude entity: Capitalized words / known tokens
    entities = sorted(
        {
            w.strip(".,:;()[]\"'")
            for w in re.findall(r"\b[A-Z][A-Za-z0-9_.-]{2,}\b", cleaned)
        }
    )[:12]
    topics: list[str] = []
    low = cleaned.lower()
    for kw in (
        "upgrade",
        "security",
        "session",
        "memory",
        "deploy",
        "version",
        "branch",
        "mcp",
        "vault",
        "todo",
        "install",
    ):
        if kw in low:
            topics.append(kw)
    if not topics:
        topics = ["general"]
    importance = 0.7 if any(t in topics for t in ("security", "upgrade", "version")) else 0.5
    if source:
        topics = list(dict.fromkeys(topics + ["sourced"]))
    return {
        "summary": summary or "empty",
        "entities": entities[:10],
        "topics": topics[:6],
        "importance": importance,
        "raw_text": cleaned[:8000],
    }


def heuristic_consolidate(memories: list[dict[str, Any]]) -> dict[str, Any]:
    if len(memories) < 2:
        return {
            "summary": "Not enough memories to consolidate",
            "insight": "",
            "source_ids": [m["id"] for m in memories],
            "connections": [],
        }
    ids = [int(m["id"]) for m in memories]
    topics: list[str] = []
    for m in memories:
        topics.extend(m.get("topics") or [])
    topic_set = sorted(set(topics))[:8]
    summary = (
        f"Consolidated {len(memories)} memories. Themes: {', '.join(topic_set) or 'mixed'}."
    )
    insight = (
        f"Cross-link {len(memories)} recent items around: "
        f"{', '.join(topic_set[:3]) or 'project state'}."
    )
    connections = []
    for i in range(len(ids) - 1):
        connections.append(
            {
                "from_id": ids[i],
                "to_id": ids[i + 1],
                "relationship": "related_in_window",
            }
        )
    return {
        "summary": summary,
        "insight": insight,
        "source_ids": ids,
        "connections": connections,
    }


def heuristic_query(
    question: str,
    memories: list[dict[str, Any]],
    consolidations: list[dict[str, Any]],
) -> str:
    q = question.lower()
    # Include version-like tokens (1.9.6) and alphanumerics
    tokens = set(re.findall(r"[a-z]{3,}|[0-9]+(?:\.[0-9]+)+", q))
    hits = []
    for m in memories:
        blob = (
            f"{m.get('summary', '')} {m.get('raw_text', '')} "
            f"{' '.join(m.get('topics') or [])} {m.get('source', '')}"
        ).lower()
        score = sum(1 for tok in tokens if tok in blob)
        # boost exact phrase fragments
        for frag in ("upgrade", "version", "open", "p1", "master", "1.9.6", "memory"):
            if frag in q and frag in blob:
                score += 1
        if score:
            hits.append((score, m))
    hits.sort(key=lambda x: (-x[0], -float(x[1].get("importance") or 0)))
    if not hits and not consolidations:
        return "No relevant memories found. Ingest context or drop files in reports/memory/inbox/."
    lines = [f"Answer (heuristic) for: {question}", ""]
    if hits:
        lines.append("From memories:")
        for score, m in hits[:8]:
            lines.append(f"- [Memory {m['id']}] {m.get('summary')} (score={score})")
    else:
        lines.append("No direct memory keyword hits; showing recent:")
        for m in memories[:5]:
            lines.append(f"- [Memory {m['id']}] {m.get('summary')}")
    if consolidations:
        lines.append("")
        lines.append("Insights:")
        for c in consolidations[:5]:
            lines.append(f"- {c.get('insight') or c.get('summary')}")
    return "\n".join(lines)


def llm_ingest(text: str, source: str, model_pick: dict[str, Any]) -> dict[str, Any]:
    cleaned = scrub_text(text)
    if model_pick.get("backend") != "ollama" or model_pick.get("status") not in (
        "ready",
        "forced",
        "forced_unknown",
    ):
        out = heuristic_ingest(cleaned, source)
        out["backend"] = "heuristic"
        return out
    ollama_name = model_pick.get("ollama_name") or model_pick.get("id")
    prompt = (
        "Extract structured memory as JSON only with keys: "
        "summary (string 1-2 sentences), entities (array of strings), "
        "topics (array 2-4 strings), importance (0.0-1.0).\n"
        f"Source: {source}\n\nContent:\n{cleaned[:6000]}\n"
    )
    try:
        raw = _ollama_generate(str(ollama_name), prompt)
        data = _extract_json_obj(raw) or {}
        out = {
            "summary": str(data.get("summary") or heuristic_ingest(cleaned)["summary"]),
            "entities": list(data.get("entities") or [])[:12],
            "topics": list(data.get("topics") or [])[:6],
            "importance": float(data.get("importance") or 0.5),
            "raw_text": cleaned[:8000],
            "backend": "ollama",
            "model": ollama_name,
        }
        return out
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        out = heuristic_ingest(cleaned, source)
        out["backend"] = "heuristic_fallback"
        return out


def llm_consolidate(
    memories: list[dict[str, Any]], model_pick: dict[str, Any]
) -> dict[str, Any]:
    if model_pick.get("backend") != "ollama" or model_pick.get("status") not in (
        "ready",
        "forced",
        "forced_unknown",
    ):
        out = heuristic_consolidate(memories)
        out["backend"] = "heuristic"
        return out
    ollama_name = model_pick.get("ollama_name") or model_pick.get("id")
    payload = [
        {
            "id": m["id"],
            "summary": m.get("summary"),
            "topics": m.get("topics"),
            "entities": m.get("entities"),
        }
        for m in memories
    ]
    prompt = (
        "Consolidate these memories. Return JSON only with keys: "
        "summary (string), insight (string), source_ids (array of int), "
        "connections (array of {from_id,to_id,relationship}).\n"
        f"Memories:\n{json.dumps(payload, indent=2)}\n"
    )
    try:
        raw = _ollama_generate(str(ollama_name), prompt)
        data = _extract_json_obj(raw) or {}
        source_ids = data.get("source_ids") or [m["id"] for m in memories]
        return {
            "summary": str(data.get("summary") or ""),
            "insight": str(data.get("insight") or ""),
            "source_ids": [int(x) for x in source_ids],
            "connections": list(data.get("connections") or []),
            "backend": "ollama",
            "model": ollama_name,
        }
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        out = heuristic_consolidate(memories)
        out["backend"] = "heuristic_fallback"
        return out


def llm_query(
    question: str,
    memories: list[dict[str, Any]],
    consolidations: list[dict[str, Any]],
    model_pick: dict[str, Any],
) -> str:
    if model_pick.get("backend") != "ollama" or model_pick.get("status") not in (
        "ready",
        "forced",
        "forced_unknown",
    ):
        return heuristic_query(question, memories, consolidations)
    ollama_name = model_pick.get("ollama_name") or model_pick.get("id")
    mem_payload = [
        {"id": m["id"], "summary": m.get("summary"), "topics": m.get("topics")}
        for m in memories[:40]
    ]
    cons_payload = [
        {"insight": c.get("insight"), "summary": c.get("summary")}
        for c in consolidations[:10]
    ]
    prompt = (
        "Answer using ONLY the memories and consolidations. Cite [Memory N]. "
        "If nothing relevant, say so.\n"
        f"Question: {question}\n"
        f"Memories: {json.dumps(mem_payload)}\n"
        f"Consolidations: {json.dumps(cons_payload)}\n"
    )
    try:
        # plain text response (not forcing json)
        host = resolve_ollama_host()
        url = f"{host}/api/generate"
        body = json.dumps(
            {
                "model": str(ollama_name),
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = str(payload.get("response") or "").strip()
        return text or heuristic_query(question, memories, consolidations)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return heuristic_query(question, memories, consolidations)


def resolve_backend(role: str, root: Path) -> dict[str, Any]:
    pick = pick_model_for_role(role, root=root)
    api = detect_api()
    pick["ollama_api"] = api.get("ollama_api")
    pick["ollama_models_count"] = api.get("ollama_models_count")
    return pick
