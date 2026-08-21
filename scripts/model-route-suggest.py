#!/usr/bin/env python3
"""Suggest free / open-source LLM when task tier is low (never silent-switch).

Open-source (Ollama) is preferred. Cloud free is secondary fallback.
Usage:
  python3 scripts/model-route-suggest.py [--task TEXT] [--chain-id ID] [--platform grok] [--json]
  ORCHESTRATOR_MODEL_ROUTE_OFFER=0  # suppress offer (still prints stay)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from _engine.ollama_detect import detect_api, evaluate  # noqa: E402

CATALOG_PATH = ROOT / "scripts" / "model-route" / "catalog.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Minimal fallback parser for catalog shape (tests still use pyyaml in CI)
        return _minimal_yaml(text)


def _minimal_yaml(text: str) -> dict[str, Any]:
    """Very small subset if PyYAML missing — enough for unit tests with mock."""
    return {
        "oss_models": [
            {
                "id": "llama3.2:3b",
                "tags": ["llama3.2:3b", "llama3.2"],
                "fits": ["low"],
                "license": "open_weights",
            }
        ],
        "free_cloud": [{"id": "gemini-flash", "surface": "gemini", "label": "Gemini Flash"}],
        "never_free_chain_ids": ["security-audit", "orchestrator"],
        "high_keywords": ["security", "production", "deploy"],
        "low_keywords": ["status", "list", "todo", "session-start"],
        "platform_how": {"default": "Use Ollama or free tier picker."},
    }


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    p = path or CATALOG_PATH
    if not p.is_file():
        raise FileNotFoundError(f"catalog missing: {p}")
    return _load_yaml(p)


def assert_oss_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    oss = catalog.get("oss_models") or []
    if not isinstance(oss, list) or not oss:
        raise ValueError("catalog must define non-empty oss_models (open-source first)")
    open_weights = [
        m
        for m in oss
        if isinstance(m, dict) and str(m.get("license") or "") == "open_weights"
    ]
    if not open_weights:
        raise ValueError("catalog oss_models must include license: open_weights entries")
    return open_weights


def resolve_chain_tier(root: Path, chain_id: str | None) -> str | None:
    if not chain_id:
        return None
    reg = root / "chains" / "registry.yaml"
    if not reg.is_file():
        return None
    text = reg.read_text(encoding="utf-8", errors="replace")
    # Find chain block by id
    pat = re.compile(
        rf"(?m)^- id:\s*{re.escape(chain_id)}\s*\n((?:  .*\n)*)",
    )
    m = pat.search(text)
    if not m:
        return None
    block = m.group(1)
    tm = re.search(r"token_tier:\s*(\w+)", block)
    return tm.group(1).lower() if tm else None


def infer_demand(
    *,
    task: str,
    chain_id: str | None,
    chain_tier: str | None,
    catalog: dict[str, Any],
) -> str:
    """Return low | medium | high."""
    never = {str(x) for x in (catalog.get("never_free_chain_ids") or [])}
    if chain_id and chain_id in never:
        return "high"
    t = (task or "").lower()
    for kw in catalog.get("high_keywords") or []:
        if str(kw).lower() in t:
            return "high"
    if chain_tier == "high":
        return "high"
    if chain_tier == "medium":
        # medium stays unless strongly low-keyword
        for kw in catalog.get("low_keywords") or []:
            if str(kw).lower() in t:
                return "low"
        return "medium"
    for kw in catalog.get("low_keywords") or []:
        if str(kw).lower() in t:
            return "low"
    if chain_tier == "low":
        return "low"
    if not t and not chain_id:
        return "low"
    return "medium"


def _norm_tag(name: str) -> str:
    return name.strip().lower()


def match_oss_installed(
    oss_models: list[dict[str, Any]], installed: list[str], *, demand: str
) -> dict[str, Any] | None:
    installed_l = [_norm_tag(x) for x in installed]
    for entry in oss_models:
        fits = [str(f).lower() for f in (entry.get("fits") or ["low"])]
        if demand == "high":
            continue
        if demand == "medium" and "medium" not in fits and "low" not in fits:
            continue
        tags = entry.get("tags") or [entry.get("id")]
        for tag in tags:
            tl = _norm_tag(str(tag))
            for inst in installed_l:
                if inst == tl or inst.startswith(tl + ":") or tl.startswith(inst.split(":")[0]):
                    if inst == tl or tl in inst or inst.split(":")[0] == tl.split(":")[0]:
                        return {**entry, "matched_tag": inst if inst in installed else tag}
        # exact tag present
        for tag in tags:
            if _norm_tag(str(tag)) in installed_l:
                return {**entry, "matched_tag": str(tag)}
    # looser: any installed name contains catalog id base
    for entry in oss_models:
        base = _norm_tag(str(entry.get("id") or "")).split(":")[0]
        for inst in installed_l:
            if base and base in inst:
                return {**entry, "matched_tag": inst}
    return None


def pick_free_cloud(catalog: dict[str, Any], platform: str) -> dict[str, Any] | None:
    clouds = catalog.get("free_cloud") or []
    plat = (platform or "default").lower()
    for c in clouds:
        if not isinstance(c, dict):
            continue
        if str(c.get("surface") or "").lower() == plat:
            return c
    return clouds[0] if clouds and isinstance(clouds[0], dict) else None


def platform_how(catalog: dict[str, Any], platform: str) -> str:
    how = catalog.get("platform_how") or {}
    if not isinstance(how, dict):
        return "Use Ollama OSS or free-tier picker (docs/guides/local-ollama.md)."
    return str(
        how.get(platform)
        or how.get("default")
        or "Use Ollama OSS or free-tier picker (docs/guides/local-ollama.md)."
    )


def offer_suppressed() -> bool:
    return os.environ.get("ORCHESTRATOR_MODEL_ROUTE_OFFER", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    )


def build_suggestion(
    *,
    root: Path,
    task: str,
    chain_id: str | None,
    platform: str,
    catalog: dict[str, Any] | None = None,
    ollama_report: dict[str, Any] | None = None,
    installed_models: list[str] | None = None,
) -> dict[str, Any]:
    cat = catalog or load_catalog()
    oss_list = assert_oss_catalog(cat)
    chain_tier = resolve_chain_tier(root, chain_id)
    demand = infer_demand(
        task=task, chain_id=chain_id, chain_tier=chain_tier, catalog=cat
    )

    if ollama_report is None:
        try:
            ollama_report = evaluate(root)
        except Exception as exc:
            ollama_report = {"ollama_api": "unreachable", "ollama_api_note": str(exc)}

    if installed_models is None:
        installed_models = list(ollama_report.get("ollama_model_names") or [])
        if not installed_models and ollama_report.get("ollama_api") == "reachable":
            # ensure names from direct API if evaluate omitted them
            api = detect_api()
            installed_models = list(api.get("ollama_model_names") or [])
            ollama_report = {**ollama_report, **api}

    oss_ready = (
        str(ollama_report.get("ollama_api") or "") == "reachable"
        and bool(installed_models)
    )

    out: dict[str, Any] = {
        "tier": chain_tier or "unknown",
        "demand": demand,
        "current": "frontier",
        "oss_ready": oss_ready,
        "oss_models_installed": installed_models,
        "recommend": "stay",
        "recommend_kind": "stay",
        "switch_options": ["stay"],
        "how": "",
        "message": "",
        "offer": False,
        "chain_id": chain_id,
        "platform": platform,
    }

    if offer_suppressed() or demand == "high":
        out["message"] = "model_route demand=high or offer off — stay on current model"
        out["how"] = "Keep current frontier/host model."
        return out

    if demand == "medium" and not oss_ready:
        out["message"] = "model_route demand=medium — stay (OSS not ready)"
        out["how"] = "Optional later: bash scripts/install-ollama.sh"
        return out

    matched = match_oss_installed(oss_list, installed_models, demand=demand) if oss_ready else None

    if matched:
        tag = str(matched.get("matched_tag") or matched.get("id"))
        out["recommend"] = f"oss:{tag}"
        out["recommend_kind"] = "oss"
        out["switch_options"] = ["stay", "oss", "free-cloud"]
        out["offer"] = True
        out["how"] = (
            f"Open-source (Ollama): use model `{tag}`. "
            + platform_how(cat, platform)
        )
        out["message"] = (
            f"Low/medium task — free open-source model available: {tag}. "
            f"Reply: stay | oss | free-cloud"
        )
        cloud = pick_free_cloud(cat, platform)
        if cloud:
            out["free_cloud"] = cloud
        return out

    # OSS not installed
    preferred = str(oss_list[0].get("id") or "llama3.2:3b")
    out["recommend"] = f"install-oss:{preferred}"
    out["recommend_kind"] = "install-oss"
    out["switch_options"] = ["stay", "install-oss", "free-cloud"]
    out["offer"] = demand == "low"
    cloud = pick_free_cloud(cat, platform)
    if cloud:
        out["free_cloud"] = cloud
    out["how"] = (
        f"Install open-source path: `bash scripts/install-ollama.sh` then "
        f"`ollama pull {preferred}`. See docs/guides/local-ollama.md. "
        + platform_how(cat, platform)
    )
    if demand == "low":
        out["message"] = (
            f"Low-tier task — free open-source option: install Ollama + pull {preferred}. "
            f"Reply: stay | install-oss | free-cloud"
        )
    else:
        out["message"] = "model_route: OSS not ready; staying unless you install-oss"
        out["offer"] = False
        out["recommend"] = "stay"
        out["recommend_kind"] = "stay"
        out["switch_options"] = ["stay"]
    return out


def format_text(s: dict[str, Any]) -> str:
    lines = [
        f"model_route tier={s.get('tier')} demand={s.get('demand')} current={s.get('current')}",
        f"oss_ready={'yes' if s.get('oss_ready') else 'no'} "
        f"models={','.join(s.get('oss_models_installed') or []) or '—'}",
        f"recommend={s.get('recommend')}",
        f"switch: {' | '.join(s.get('switch_options') or ['stay'])}",
        f"how: {s.get('how') or '—'}",
    ]
    if s.get("message"):
        lines.append(f"ask: {s['message']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--task", default="", help="User task text for keyword tier")
    p.add_argument("--chain-id", default=None)
    p.add_argument("--platform", default="grok", help="Host surface: grok|claude|cursor|gemini|copilot")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--mock-json",
        default=None,
        help="Path to mock ollama report JSON (tests)",
    )
    args = p.parse_args(argv)

    mock_path = args.mock_json or os.environ.get("ORCHESTRATOR_MODEL_ROUTE_MOCK")
    ollama_report = None
    installed = None
    if mock_path:
        data = json.loads(Path(mock_path).read_text(encoding="utf-8"))
        ollama_report = data.get("ollama") or data
        installed = data.get("installed_models") or ollama_report.get("ollama_model_names")

    cat = load_catalog()
    suggestion = build_suggestion(
        root=args.root.resolve(),
        task=args.task,
        chain_id=args.chain_id,
        platform=args.platform,
        catalog=cat,
        ollama_report=ollama_report,
        installed_models=installed,
    )
    if args.json:
        print(json.dumps(suggestion, indent=2))
    else:
        sys.stdout.write(format_text(suggestion))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
