# Session context envelope — token budget (before / after)

**Branch / feature:** `feature/session-context-envelope-2026-07-17`  
**Measured on:** orchestrator template repo (2026-07-17)  
**Estimator:** `max(chars/4, words×1.3)` — approximate GPT-style English tokens, not a billable invoice.  
**Purpose:** show that spin-up can be **more context-aware** while **cutting** model-visible tokens.

## Platforms (same script, thin local pointers)

| Platform | Entry | Procedure |
|----------|--------|-----------|
| **Grok** | `.grok/skills/session-context-envelope/SKILL.md` | `python3 scripts/session-context-envelope.py --write` |
| **Claude Code** | `.claude/commands/session-context-envelope.md` + `CLAUDE.md` | same script |
| **GitHub Copilot** | `.github/skills/…` + `.copilot/skills/…` | same script |
| **Gemini** | `.gemini/instructions/…` + `.gemini/prompts/session-context-envelope.md` | same script |
| **Cursor** | `.cursor/rules/session-context-envelope.mdc` + `.cursor/README.md` | same script |

Canonical implementation: `scripts/session-context-envelope.py` + `scripts/_engine/session_envelope.py`.  
Artifacts: `reports/sessions/context-latest.txt` (compact) · `context-latest.json` (full).

---

## What “cost” means here

We measure **tokens the model is asked to load or emit as session context**, not:

- Host CPU for running scripts (cheap; outside the context window)
- One-time skill *discovery* metadata (name + description only)

### Included in budgets

| Kind | Example |
|------|---------|
| Skill/procedure body | Full standup SKILL.md if agent Reads it |
| Script stdout injected into the chat | resume check JSON, detect JSON, vault brief |
| Compact envelope text | CTX block |
| Optional expand payload | MCP start option lines |

### Excluded

| Kind | Why |
|------|-----|
| Full `docs/codebase/*` deep load | Same rules before/after (`max_cache_files`) |
| Security sweep *report body* | Pointer only unless `expand: sec` |
| Chain registry full Read | Forbidden in lean mode either way |

---

## Measured results (this repo, 2026-07-17)

| Scenario | ~Tokens (model-visible) | Notes |
|----------|------------------------:|-------|
| **BEFORE — naive full standup** | **~8 580** | Loads standup (~4.9k) + load-cache (~1.1k) + resume skill/ref (~1.2k) + multi-script dumps (~1.4k) |
| **BEFORE — resume-first disciplined** | **~2 520** | Resume skill + ref + multi-script dumps; **no** full standup body |
| **AFTER — envelope spin-up** | **~675** | Thin skill (~440) + compact CTX (~230) |
| **AFTER — mid-session reuse** | **~230** | Re-print / re-read `context-latest.txt` only |
| **AFTER — with MCP expand** | **~800** | Thin skill + compact + `expand_payload.mcp` |

### Savings vs naive full standup

| Path | Before | After | Δ tokens | Δ % |
|------|-------:|------:|---------:|----:|
| Spin-up (first briefing) | ~8 580 | ~675 | **−7 900** | **~−92%** |
| Mid-session “what’s my context?” | ~2 520+ | ~230 | **−2 300** | **~−91%** |

### Savings vs best prior practice (resume-first)

| Path | Before | After | Δ tokens | Δ % |
|------|-------:|------:|---------:|----:|
| Spin-up with resume-first | ~2 520 | ~675 | **−1 840** | **~−73%** |

---

## Component breakdown

### Before (resume-first + identity/MCP work, multi-script)

| Component | ~Tokens | Role |
|-----------|--------:|------|
| `session-resume` skill | ~420 | Procedure |
| `resume-first.md` | ~740 | Gate rules |
| `session-resume-brief.py check --json` | ~420 | Card + gate |
| `detect-project-runtime.sh --json --with-manifest-identity` | ~540 | Runtime + MCP + options text |
| `check-project-manifest.py --json` | ~120 | Identity |
| `session-vault-brief.py` (text head) | ~280 | Vault lessons |
| **Subtotal scripts** | **~1 360** | |
| **Subtotal procedure** | **~1 160** | |
| **Total disciplined** | **~2 520** | |

If the agent also Reads full `daily-standup-with-cache/SKILL.md` (~4 940) + load-cache (~1 120), total jumps to **~8 580**.

### After (envelope)

| Component | ~Tokens | Role |
|-----------|--------:|------|
| Thin skill `session-context-envelope` | ~440 | Shared rules (all platforms) |
| Compact CTX (`context-latest.txt`) | ~230 | All live facts as enums + open/next |
| **Total spin-up** | **~675** | |
| Mid-session file only | ~230 | No skill re-read required |
| Optional `--expand` MCP options | +~120 | Only when `expand: mcp_start` |

**Context still present (not lost):**

- Manifest identity (`ok` / `template_residue` / `warn`)
- MCP ready + **dev_only** policy + env_safe
- Branch, sync, stack@runtime
- Security overall (PASS/WARN/FAIL) + pointer
- Vault OK
- Open items + next action
- Pointers to TODO, resume card, sweep report, manifest

---

## Reasoning (why after is cheaper *and* more aware)

1. **Compute outside the model**  
   Identity, runtime, MCP policy, vault verify, and open-item extraction run in Python/bash. The model does not re-derive them from files.

2. **One artifact instead of four dumps**  
   Before: separate JSON/text streams (resume + detect + identity + vault) with overlapping prose.  
   After: one fixed schema; compact is the only default surface.

3. **Enums over essays**  
   `identity=ok`, `mcp=pending@dev_only`, `sec=PASS` beat multi-paragraph explanations when status is green.

4. **Progressive disclosure**  
   `expand: none` → stop.  
   `expand: mcp_start` → options only on demand.  
   Red statuses (`template_residue`, `blocked`, `FAIL`) unlock payloads; green does not.

5. **Procedure collapse**  
   Full standup skill is a **novel** (~5k tokens). The envelope skill is a **postcard** (~440).  
   Agents are instructed: if envelope is enough, **do not Read** the standup body.

6. **Cross-platform without N× skill novels**  
   Gemini / Cursor / Claude / Copilot / Grok all call the **same** script. Platform files are thin pointers (~50–150 tokens if loaded), not forked procedures.

7. **Disk is the second brain**  
   `context-latest.json` is reusable mid-session and by other tools without regenerating chat history.

---

## Agent contract (enforce this to keep the savings)

```text
1. Run: python3 scripts/session-context-envelope.py --write
   ORDER inside script: fetch → remote_last switch/pull (clean) → THEN resume check/card
   Real WIP blocks switch; context-latest/session-sweep soft-dirty OK
2. Print compact CTX only — never restate in long prose
3. ALWAYS surface check + resume card when present (even if stale)
4. ALWAYS surface ver= and behind_develop — wrong base is a first-class session fact
5. If off remote_last → surface align recommendations + off_remote_last expand
6. If expand is only pickup/mcp_start/resume_card → one-line offer; dump expand_payload if needed
7. Do not Read daily-standup-with-cache SKILL body on the green path
8. MCP is develop-only; never on public hosts
9. identity≠ok ⇒ do not trust stack/runtime
10. session-end + eod-shutdown MUST write rich resume cards AND print next-start
    remote_last-first order reminder
```

Violations (skipping card, re-loading standup skill, dumping full detect JSON, rewriting the envelope as a blog post) **erase** most of the savings **or** lose continuity.

## Pickup + correct base (why this is on every app)

Session-start is not only “load cache” — it is **continuity**:

| Signal | Source | Behaviour |
|--------|--------|-----------|
| `remote_last` first | `resume-branch.sh --apply` | **fetch → switch/pull team tip** when clean; block real WIP |
| Resume card (after switch) | `session-resume-brief.py check` | Lean only when fresh **and** Branch matches checkout |
| Off tip | `align_recommendations` | Status vs remote_last + how to rejoin team tip |
| `operator_last_branch` | vault pointer | Cross-machine last branch (secondary; not switch authority) |
| `ver=` / `behind_develop` | `VERSION` + `origin/develop` | Merge/rebase before release-sensitive work |
| `ver_open` / `ver_ask` | Marketplace VSIX line vs `VERSION` | Warn + offer retarget; never auto-rewrite |
| Next-start reminder | session-end / eod card write | Rich card always embeds remote_last-first order |

These belong in the **envelope**, not as optional agent memory.

---

## One-shot spin-up (preferred agent command)

Avoid chaining 5–6 separate scripts into the model context:

```bash
# Single model-visible artifact (~CTX + situation only)
python3 scripts/session-spinup-bundle.py
# → print reports/sessions/spinup-latest.txt only
```

| Artifact | Role | Model should |
|----------|------|----------------|
| `spinup-latest.txt` | CTX + situation | **Print once** at session-start |
| `situation-latest.txt` | Where / in-flight / repetition | Reuse; `--use-cache` if inputs unchanged |
| `context-latest.json` | Full envelope for tools | Not dumped into chat |
| `situation-latest.json` | Machine fields | Not dumped into chat |

**Do not** re-run vault-brief + wiki-brief + situation + resume-check as separate agent Reads after spinup — that re-adds ~3–4k tokens of JSON.

### Fingerprint cache

`session-situation-brief.py --use-cache` skips rebuild when TODO/resume/STATE/vault/branch fingerprint matches (max age 1h). Envelope does a full rebuild once; later chain steps hit cache.

### Version identity (avoid disparity)

| Field | Role |
|-------|------|
| **`VERSION`** | **Single source of truth** (full identity, e.g. `1.9.1` or `1.9.0-pre.5`) |
| `scripts/orchestrator-template-version` | Deployed stamp apps read — **must = VERSION** |
| `package.json` version | npm mirror — **must = VERSION** |
| `bundle-hashes.json` version | Bundle stamp — **must = VERSION** |
| hatch wheel | May be **core-only** `X.Y.Z` (see `pyproject.toml`) — intentional |

```bash
python3 scripts/check-version-alignment.py
# fix mirrors: node scripts/npm/sync-version.js && python3 scripts/orchestrator-bundle-hash.py
```

Session upgrade compare is **pre-release aware** (`1.9.0-pre.5` > `pre.3`; final `1.9.0` > any pre).

### Guardrails one-liner (prompt injection)

```bash
python3 scripts/session-guardrails-check.py          # one line: guardrails=PASS|WARN|FAIL
python3 scripts/session-guardrails-check.py --scan   # + capped TODO/vault sample
```

Included in `session-spinup-bundle.py`. Guide: `docs/guides/prompt-injection-installed-apps.md`.

### Security sweep fingerprint

`session-security-sweep.sh` **must re-run when the security-relevant tree fingerprint changes**
(branch, HEAD, dirty paths, `.env*` mtimes). Session spin-up noise
(`context-latest`, `situation-latest`, `spinup-*`) is **excluded** from that fingerprint.

| Condition | Action |
|-----------|--------|
| Fingerprint **changed** | Full re-scan (always) |
| Same-day report **PASS** + fingerprint match | **Reuse** report (cache hit) |
| Prior **FAIL** / **WARN** | Full re-scan even if fingerprint matches |
| `--force` | Full re-scan |
| `--no-cache` | Full re-scan |

### Vector DB?

See `scripts/session-vector-probe.py` and `reports/research/vector-session-probe-*.md`.  
**Default: reject/defer** for this meta-repo — use token+BOW hybrid in situation brief; revisit if vault ≫ thousands of events.

## How to re-measure

```bash
# Preferred one-shot
python3 scripts/session-spinup-bundle.py --json   # tokens_est field

# Compact size
python3 scripts/session-context-envelope.py --write
wc -c reports/sessions/context-latest.txt

# Rough tokens
python3 - <<'PY'
from pathlib import Path
t = Path("reports/sessions/context-latest.txt").read_text()
print("tokens~", max(len(t)//4, int(len(t.split())*1.3)))
PY

# Compare skill bodies
wc -c .grok/skills/daily-standup-with-cache/SKILL.md \
     .grok/skills/session-context-envelope/SKILL.md
```

---

## Related

- Identity engine: `scripts/_engine/manifest_identity.py`
- MCP policy: `scripts/_engine/mcp_runtime_policy.py`
- Envelope engine: `scripts/_engine/session_envelope.py`
- Chain: `session-start` in `chains/registry.yaml` (steps `resume-first` → `envelope` → lean `standup`)
