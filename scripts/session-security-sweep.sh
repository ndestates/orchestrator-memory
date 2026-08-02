#!/usr/bin/env bash
# session-security-sweep.sh — lean **active-app** security + Cyber Essentials
# signals for /chain session-start. Report-only; never mutates git or auto-fixes.
#
# Default: scan **this repository only** (secrets guard + CSE). Does not walk
# ~/projects or any sibling apps. Fleet multi-repo is opt-in via --all-repos.
#
# Always writes a human report under reports/security/session-sweep-YYYY-MM-DD.md
# (unless --no-report). Agents MUST cite report_path in the session-start briefing.
#
# Usage:
#   bash scripts/session-security-sweep.sh
#   bash scripts/session-security-sweep.sh --active-only   # same as default
#   bash scripts/session-security-sweep.sh --all-repos [PROJECTS_ROOT]
#   bash scripts/session-security-sweep.sh --json
#   bash scripts/session-security-sweep.sh --no-report
#   bash scripts/session-security-sweep.sh --force         # always full scan
#   bash scripts/session-security-sweep.sh --no-cache      # ignore fingerprint reuse
#
# Fingerprint policy (token-efficient session-start):
#   - Compute security-relevant tree fingerprint (branch + HEAD + porcelain,
#     excluding session spin-up noise: context-latest, situation-latest, spinup-*).
#   - If fingerprint **changes** → always re-run (surface may have new secrets/config).
#   - If fingerprint **unchanged** and same-day report overall=PASS → reuse (cite path).
#   - If last overall was FAIL or WARN → always re-run.
#   - --force always re-runs.
#
# Exit: 0 always (findings are printed; agents surface FAIL/WARN + report path).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECTS_ROOT="${HOME}/projects"
# Default: this app only. Fleet multi-repo is opt-in (--all-repos).
ACTIVE_ONLY=1
JSON=0
WRITE_REPORT=1
FORCE=0
USE_CACHE=1
for arg in "$@"; do
  case "$arg" in
    --active-only) ACTIVE_ONLY=1 ;;
    --all-repos|--fleet) ACTIVE_ONLY=0 ;;
    --json) JSON=1 ;;
    --no-report) WRITE_REPORT=0 ;;
    --force) FORCE=1 ;;
    --no-cache) USE_CACHE=0 ;;
    -*) ;;
    *) PROJECTS_ROOT="$arg" ;;
  esac
done

# --- Security-relevant fingerprint (re-run sweep when this changes) ---
_security_fingerprint() {
  local branch head porcelain filtered
  branch="$(git -C "$ROOT" branch --show-current 2>/dev/null || echo unknown)"
  head="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo none)"
  porcelain="$(git -C "$ROOT" status --porcelain 2>/dev/null || true)"
  # Drop session spin-up noise — not security surface for secrets/CSE delta
  filtered="$(printf '%s\n' "${porcelain}" | grep -vE \
    'reports/sessions/context-latest\.|reports/sessions/situation-latest\.|reports/sessions/spinup-latest\.|reports/sessions/situation-fingerprint|reports/security/session-sweep-' \
    || true)"
  # High-risk path presence (env files)
  local env_sig=""
  local f
  for f in .env .env.local .env.production; do
    if [[ -f "${ROOT}/${f}" ]]; then
      env_sig+="${f}:$(stat -c '%Y:%s' "${ROOT}/${f}" 2>/dev/null || stat -f '%m:%z' "${ROOT}/${f}" 2>/dev/null || echo x);"
    fi
  done
  printf 'branch=%s\nhead=%s\nporcelain=%s\nenv=%s\nactive_only=%s\n' \
    "${branch}" "${head}" "${filtered}" "${env_sig}" "${ACTIVE_ONLY}" \
    | sha256sum 2>/dev/null | awk '{print $1}' \
    || printf 'branch=%s\nhead=%s\nporcelain=%s\nenv=%s\nactive_only=%s\n' \
      "${branch}" "${head}" "${filtered}" "${env_sig}" "${ACTIVE_ONLY}" \
      | sha1sum 2>/dev/null | awk '{print $1}'
}

FP_NOW="$(_security_fingerprint)"
day_utc="$(date -u +%Y-%m-%d)"
report_rel="reports/security/session-sweep-${day_utc}.md"
report_abs="${ROOT}/${report_rel}"
fp_file="${ROOT}/reports/security/session-sweep-fingerprint.txt"
meta_file="${ROOT}/reports/security/session-sweep-latest.json"
cache_hit=no
cache_reason=""

if [[ "${FORCE}" -eq 1 ]]; then
  cache_reason="force"
elif [[ "${USE_CACHE}" -eq 0 ]]; then
  cache_reason="no_cache"
elif [[ ! -f "${report_abs}" ]] || [[ ! -f "${meta_file}" ]]; then
  cache_reason="no_prior_report"
else
  prior_fp="$(head -1 "${fp_file}" 2>/dev/null || true)"
  prior_overall="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('overall',''))" "${meta_file}" 2>/dev/null || true)"
  if [[ -z "${prior_fp}" ]]; then
    cache_reason="no_prior_fp"
  elif [[ "${prior_fp}" != "${FP_NOW}" ]]; then
    cache_reason="fingerprint_changed"
  elif [[ "${prior_overall}" != "PASS" ]]; then
    cache_reason="prior_${prior_overall:-unknown}_must_rescan"
  else
    cache_hit=yes
    cache_reason="fingerprint_match_pass"
  fi
fi

if [[ "${cache_hit}" == "yes" ]]; then
  # Reuse same-day PASS report — still surface path + overall for briefing
  report_path="${report_rel}"
  if [[ "${JSON}" -eq 1 ]]; then
    python3 - "${meta_file}" "${FP_NOW}" "${cache_reason}" "${report_path}" <<'PY'
import json, sys
meta_path, fp, reason, rpath = sys.argv[1:5]
try:
    d = json.load(open(meta_path, encoding="utf-8"))
except Exception:
    d = {"overall": "PASS"}
d["cache_hit"] = True
d["cache_reason"] = reason
d["fingerprint"] = fp
d["report_path"] = rpath
print(json.dumps(d, indent=2))
PY
    exit 0
  fi
  python3 - "${meta_file}" "${FP_NOW}" "${cache_reason}" "${report_path}" "${ROOT}" <<'PY'
import json, sys
meta_path, fp, reason, rpath, root = sys.argv[1:6]
try:
    d = json.load(open(meta_path, encoding="utf-8"))
except Exception:
    d = {}
print("=== Session security sweep ===")
print("cache_hit=yes")
print(f"cache_reason={reason}")
print(f"fingerprint={fp}")
print(f"root_active={root}")
print(f"overall={d.get('overall', 'PASS')}")
print(f"repos_scanned={d.get('repos_scanned', 1)}")
print(f"secrets_pass={d.get('secrets_pass', 1)}")
print(f"secrets_fail={d.get('secrets_fail', 0)}")
print(f"secrets_skip={d.get('secrets_skip', 0)}")
print(f"hooks_ok={d.get('hooks_ok', 1)}")
print(f"hooks_missing={d.get('hooks_missing', 0)}")
print(f"cse_status={d.get('cse_status', 'cached')}")
print(f"cse_warns={d.get('cse_warns', 0)}")
print(f"cse_findings={d.get('cse_findings', 0)}")
print(f"cse_summary={d.get('cse_summary', 'reused same-day PASS (fingerprint unchanged)')}")
print(f"report_path={rpath}")
print("--- findings ---")
print("(none — reused PASS report; tree fingerprint unchanged)")
print(
    f"=== Sweep complete: overall={d.get('overall', 'PASS')} · "
    f"report={rpath} (cache hit; cite in session-start) ==="
)
PY
  exit 0
fi

# Full scan path (fingerprint changed, no cache, force, or prior non-PASS)
# shellcheck disable=SC2034
CACHE_MISS_REASON="${cache_reason}"

SECRETS_GUARD="${ROOT}/scripts/git-push-secrets-guard.py"
CSE_SCAN="${ROOT}/.grok/skills/cyber-security-essentials/scripts/cyber-essentials-scan.sh"
# Prefer target-local scripts when sweeping other repos
_find_guard() {
  local repo="$1"
  if [[ -f "${repo}/scripts/git-push-secrets-guard.py" ]]; then
    echo "${repo}/scripts/git-push-secrets-guard.py"
  elif [[ -f "${SECRETS_GUARD}" ]]; then
    echo "${SECRETS_GUARD}"
  else
    echo ""
  fi
}

repos_scanned=0
secrets_pass=0
secrets_fail=0
secrets_skip=0
hooks_ok=0
hooks_missing=0
declare -a FINDINGS=()
declare -a REPO_ROWS=()

_scan_repo_secrets() {
  local repo="$1"
  local name
  name="$(basename "$repo")"
  repos_scanned=$((repos_scanned + 1))

  local guard
  guard="$(_find_guard "$repo")"
  local dirty_files=()
  local status_line
  status_line="$(git -C "$repo" status --porcelain 2>/dev/null || true)"

  # Hook presence (template expectation)
  local hook_note="hooks=unknown"
  if [[ -f "${repo}/.githooks/pre-commit" ]] || [[ -f "${repo}/.git/hooks/pre-commit" ]]; then
    hooks_ok=$((hooks_ok + 1))
    hook_note="hooks=present"
  else
    hooks_missing=$((hooks_missing + 1))
    hook_note="hooks=missing"
    FINDINGS+=("WARN ${name}: no pre-commit hook (install via scripts/setup-git-hooks.sh or ensure-git-secrets-hooks.sh)")
  fi

  if [[ -z "${guard}" ]]; then
    secrets_skip=$((secrets_skip + 1))
    REPO_ROWS+=("${name}|secrets=skip|${hook_note}|no git-push-secrets-guard.py")
    return
  fi

  # Prefer dirty / untracked text files; else last commit range vs upstream if available.
  # Cap at 40 *while collecting* — never walk entire porcelain (huge dirty trees hang).
  local -a paths=()
  local dirty_cap=40
  if [[ -n "${status_line}" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      [[ ${#paths[@]} -ge ${dirty_cap} ]] && break
      # porcelain: XY path  or  XY orig -> path (bash-only; no per-line sed subshell)
      local p="${line:3}"
      if [[ "$p" == *" -> "* ]]; then
        p="${p##* -> }"
      fi
      [[ -f "${repo}/${p}" ]] && paths+=("${p}")
    done <<< "${status_line}"
  fi

  local result="pass"
  local detail=""
  if [[ ${#paths[@]} -gt 0 ]]; then
    local -a capped=("${paths[@]}")
    if ! (
      cd "$repo" && python3 "$guard" --files "${capped[@]}" >/dev/null 2>&1
    ); then
      result="FAIL"
      secrets_fail=$((secrets_fail + 1))
      detail="dirty files failed secrets guard"
      FINDINGS+=("FAIL ${name}: secrets guard failed on dirty/untracked files")
    else
      secrets_pass=$((secrets_pass + 1))
      detail="dirty files clean (${#capped[@]} scanned)"
    fi
  else
    # Clean tree: scan commits not on upstream when available
    local range=""
    local up
    up="$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
    if [[ -n "$up" ]]; then
      range="${up}..HEAD"
    elif git -C "$repo" rev-parse --verify --quiet HEAD >/dev/null; then
      # single commit peek
      range="HEAD~1..HEAD"
      git -C "$repo" rev-parse --verify --quiet HEAD~1 >/dev/null 2>&1 || range=""
    fi
    if [[ -n "$range" ]]; then
      if ! (
        cd "$repo" && python3 "$guard" --range "$range" >/dev/null 2>&1
      ); then
        result="FAIL"
        secrets_fail=$((secrets_fail + 1))
        detail="range ${range} failed secrets guard"
        FINDINGS+=("FAIL ${name}: secrets guard failed on ${range}")
      else
        secrets_pass=$((secrets_pass + 1))
        detail="range ${range} clean"
      fi
    else
      secrets_pass=$((secrets_pass + 1))
      detail="no dirty files / no range — skipped deep scan"
    fi
  fi
  REPO_ROWS+=("${name}|secrets=${result}|${hook_note}|${detail}")
}

# --- Secrets sweep: active app by default; --all-repos for fleet ---
if [[ "${ACTIVE_ONLY}" -eq 1 ]]; then
  _scan_repo_secrets "$ROOT"
elif [[ -d "${PROJECTS_ROOT}" ]]; then
  for dir in "${PROJECTS_ROOT}"/*/; do
    repo="${dir%/}"
    git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || continue
    _scan_repo_secrets "$repo"
  done
  # Always include active root if not under PROJECTS_ROOT
  case "${ROOT}" in
    "${PROJECTS_ROOT}"/*) ;;
    *)
      if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
        _scan_repo_secrets "$ROOT"
      fi
      ;;
  esac
else
  _scan_repo_secrets "$ROOT"
fi

# --- Active repo Cyber Essentials lean scan ---
cse_status="skip"
cse_summary=""
cse_warns=0
cse_findings=0
if [[ -x "${CSE_SCAN}" ]] || [[ -f "${CSE_SCAN}" ]]; then
  cse_out="$(bash "${CSE_SCAN}" "${ROOT}" 2>/dev/null || true)"
  cse_status="ran"
  # Only count real WARN lines from Control 5 etc. — not pattern text inside hits
  # and not OK lines. Format from cyber-essentials-scan: "WARN: …" at line start.
  cse_warns="$(printf '%s\n' "${cse_out}" | grep -cE '^WARN:' || true)"
  # Findings = non-empty hit lines under controls (path:line:…) — exclude section headers/OK/hints
  cse_findings="$(printf '%s\n' "${cse_out}" | grep -cE '^[./][^ ]+:[0-9]+:' || true)"
  # Compact one-liners: section headers + OK + WARN only
  cse_summary="$(printf '%s\n' "${cse_out}" | grep -E '^--- Control|^OK |^WARN:|^\(no matches\)' | head -20 | tr '\n' ' · ' | sed 's/ · $//')"
  if [[ "${cse_warns}" -gt 0 ]]; then
    FINDINGS+=("WARN active-repo CSE: ${cse_warns} WARN line(s) — open report CSE section")
  fi
  if [[ "${cse_findings}" -gt 0 ]]; then
    FINDINGS+=("WARN active-repo CSE: ${cse_findings} code/config hit(s) — review cyber-essentials-scan output")
  fi
else
  cse_status="missing_script"
  FINDINGS+=("WARN CSE: cyber-essentials-scan.sh not found under .grok/skills/")
fi

overall="PASS"
if [[ "${secrets_fail}" -gt 0 ]]; then
  overall="FAIL"
elif [[ ${#FINDINGS[@]} -gt 0 ]]; then
  overall="WARN"
fi

branch="$(git -C "$ROOT" branch --show-current 2>/dev/null || echo unknown)"
ts_utc="$(date -u +%Y-%m-%dT%H:%MZ)"
# day_utc / report paths already set above for cache check
report_path=""

if [[ "${WRITE_REPORT}" -eq 1 ]]; then
  mkdir -p "${ROOT}/reports/security"
  {
    echo "# Session security sweep — ${day_utc}"
    echo
    echo "| Field | Value |"
    echo "|-------|-------|"
    echo "| **When (UTC)** | ${ts_utc} |"
    echo "| **Overall** | **${overall}** |"
    echo "| **Active repo** | \`${ROOT}\` |"
    echo "| **Branch** | \`${branch}\` |"
    echo "| **Fingerprint** | \`${FP_NOW:0:16}…\` |"
    echo "| **Cache** | miss (${cache_reason:-full}) |"
    echo "| **Projects root** | \`${PROJECTS_ROOT}\` |"
    echo "| **Repos scanned** | ${repos_scanned} |"
    echo "| **Secrets** | pass=${secrets_pass} · fail=${secrets_fail} · skip=${secrets_skip} |"
    echo "| **Hooks** | present=${hooks_ok} · missing=${hooks_missing} |"
    echo "| **CSE** | status=${cse_status} · warns=${cse_warns} · code_hits=${cse_findings:-0} |"
    echo
    echo "## Summary for briefing"
    echo
    case "${overall}" in
      PASS) echo "Multi-repo secrets guard clean; CSE lean scan completed with no high-signal warnings." ;;
      WARN) echo "No secrets-guard FAIL, but WARN signals exist (hooks and/or CSE). Review findings below; continue session unless FAIL." ;;
      FAIL) echo "**Secrets guard failed on one or more repos.** Resolve before commit/push. CSE may also have warnings." ;;
    esac
    echo
    echo "## Per-repo"
    echo
    echo "| Project | Secrets | Hooks | Detail |"
    echo "|---------|---------|-------|--------|"
    for row in "${REPO_ROWS[@]:-}"; do
      # name|secrets=X|hooks=Y|detail
      IFS='|' read -r rname rsec rhooks rdetail <<< "${row}"
      rsec_v="${rsec#secrets=}"
      rhooks_v="${rhooks#hooks=}"
      echo "| \`${rname}\` | ${rsec_v} | ${rhooks_v} | ${rdetail} |"
    done
    echo
    echo "## Findings"
    echo
    if [[ ${#FINDINGS[@]} -gt 0 ]]; then
      for f in "${FINDINGS[@]}"; do
        echo "- ${f}"
      done
    else
      echo "- (none)"
    fi
    echo
    echo "## Cyber Essentials (lean static)"
    echo
    echo "Mode: **gap-only / static** (not UK CE certification). Full pass: \`/chain cyber-essentials-review\`."
    echo
    echo "- Status: \`${cse_status}\`"
    echo "- Warning signals: ${cse_warns}"
    echo "- Summary: ${cse_summary:-—}"
    echo
    if [[ -n "${cse_out:-}" ]]; then
      echo "### CSE scan excerpt"
      echo
      echo '```'
      echo "${cse_out}" | head -80
      echo '```'
      echo
    fi
    echo "## Operator actions"
    echo
    echo "1. Cite this report in the session-start briefing (\`overall\` + path)."
    echo "2. On **FAIL**: fix secrets findings before any commit/push."
    echo "3. On **WARN** with CSE signals: optional \`/chain cyber-essentials-review\`."
    echo "4. Missing hooks: \`bash scripts/setup-git-hooks.sh\` or \`bash scripts/ensure-git-secrets-hooks.sh\`."
    echo
    echo "---"
    echo
    echo "_Generated by \`scripts/session-security-sweep.sh\` (session-start security-hygiene)._"
  } > "${report_abs}"
  report_path="${report_rel}"
  # Persist fingerprint + meta for next session-start cache decision
  printf '%s\n' "${FP_NOW}" > "${fp_file}"
  python3 - "${meta_file}" "${overall}" "${repos_scanned}" "${secrets_pass}" \
    "${secrets_fail}" "${secrets_skip}" "${hooks_ok}" "${hooks_missing}" \
    "${cse_status}" "${cse_warns}" "${cse_findings:-0}" "${cse_summary}" \
    "${report_rel}" "${FP_NOW}" "${cache_reason:-full}" <<'PY'
import json, sys
path = sys.argv[1]
keys = [
    "overall", "repos_scanned", "secrets_pass", "secrets_fail", "secrets_skip",
    "hooks_ok", "hooks_missing", "cse_status", "cse_warns", "cse_findings",
    "cse_summary", "report_path", "fingerprint", "cache_reason",
]
vals = sys.argv[2:16]
data = dict(zip(keys, vals))
for k in (
    "repos_scanned", "secrets_pass", "secrets_fail", "secrets_skip",
    "hooks_ok", "hooks_missing", "cse_warns", "cse_findings",
):
    try:
        data[k] = int(data[k])
    except (TypeError, ValueError):
        data[k] = 0
data["cache_hit"] = False
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
fi

if [[ "${JSON}" -eq 1 ]]; then
  python3 - "$overall" "$repos_scanned" "$secrets_pass" "$secrets_fail" "$secrets_skip" \
    "$hooks_ok" "$hooks_missing" "$cse_status" "$cse_warns" "$cse_summary" "${report_path}" \
    "$FP_NOW" "$cache_reason" <<'PY'
import json, sys
overall, scanned, sp, sf, ss, hk, hm, cse, cw, csum, rpath, fp, creason = sys.argv[1:14]
print(json.dumps({
    "overall": overall,
    "cache_hit": False,
    "cache_reason": creason or "full",
    "fingerprint": fp,
    "repos_scanned": int(scanned),
    "secrets_pass": int(sp),
    "secrets_fail": int(sf),
    "secrets_skip": int(ss),
    "hooks_ok": int(hk),
    "hooks_missing": int(hm),
    "cse_status": cse,
    "cse_warns": int(cw or 0),
    "cse_summary": csum,
    "report_path": rpath or None,
}, indent=2))
PY
  for f in "${FINDINGS[@]:-}"; do
    echo "# finding: $f"
  done
  exit 0
fi

echo "=== Session security sweep ==="
echo "cache_hit=no"
echo "cache_reason=${cache_reason:-full}"
echo "fingerprint=${FP_NOW}"
echo "root_active=${ROOT}"
echo "projects_root=${PROJECTS_ROOT}"
echo "overall=${overall}"
echo "repos_scanned=${repos_scanned}"
echo "secrets_pass=${secrets_pass}"
echo "secrets_fail=${secrets_fail}"
echo "secrets_skip=${secrets_skip}"
echo "hooks_ok=${hooks_ok}"
echo "hooks_missing=${hooks_missing}"
echo "cse_status=${cse_status}"
echo "cse_warns=${cse_warns}"
echo "cse_findings=${cse_findings:-0}"
echo "cse_summary=${cse_summary}"
echo "report_path=${report_path}"
echo
echo "--- per-repo ---"
for row in "${REPO_ROWS[@]:-}"; do
  echo "$row"
done
echo
if [[ ${#FINDINGS[@]} -gt 0 ]]; then
  echo "--- findings ---"
  for f in "${FINDINGS[@]}"; do
    echo "$f"
  done
else
  echo "--- findings ---"
  echo "(none)"
fi
echo
if [[ -n "${report_path}" ]]; then
  echo "=== Sweep complete: overall=${overall} · report=${report_path} (cite in session-start briefing) ==="
else
  echo "=== Sweep complete (report-only; surface overall=${overall} in session-start briefing) ==="
fi
