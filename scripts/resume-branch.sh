#!/usr/bin/env bash
# Output the latest remote work branch for session-start / EOD resume.
# Excludes origin/develop and origin/master unless they are the only activity.
# Also reports whether the *current* checkout is up to date with its upstream.
#
# Policy (orchestrator session-start):
#   1. git fetch origin --prune (always)
#   2. Target remote_last (newest origin/* by committer date, excluding
#      develop/master)
#   3. With --apply: auto-switch + ff-only pull when the tree is clean
#   4. Session spin-up noise only (context-latest, session-sweep) is soft-dirty
#      and does not block switch — real WIP always blocks (never discard)
#   5. Resume card is read AFTER switch (envelope), not from the pre-switch branch
#   --force-dirty is accepted for compatibility but does **not** override real WIP.
#
# Usage:
#   bash scripts/resume-branch.sh              # report only
#   bash scripts/resume-branch.sh --apply      # switch to remote_last if clean
#   bash scripts/resume-branch.sh --apply --json  # reserved: same as kv lines
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

APPLY=0
FORCE_DIRTY=0
for _arg in "$@"; do
  case "${_arg}" in
    --apply|--switch) APPLY=1 ;;
    --force-dirty) FORCE_DIRTY=1 ;;
  esac
done

echo "startup_policy=fetch_then_remote_last_then_card"
git fetch origin --prune 2>/dev/null || true
echo "fetch_ok=yes"

current="$(git branch --show-current 2>/dev/null || echo unknown)"

# Per-operator last branch from vault brain (git-synced via events.jsonl)
operator=""
operator_last_branch=""
operator_pointer_found="no"
operator_branch_on_origin="no"
operator_last_ts=""
_vault_read="$(python3 "$(dirname "$0")/vault-workspace-pointer.py" --read --format shell 2>/dev/null || true)"
if [[ -n "${_vault_read}" ]]; then
  while IFS='=' read -r _k _v; do
    case "${_k}" in
      operator) operator="${_v}" ;;
      operator_last_branch) operator_last_branch="${_v}" ;;
      operator_pointer_found) operator_pointer_found="${_v}" ;;
      operator_branch_on_origin) operator_branch_on_origin="${_v}" ;;
      operator_last_ts) operator_last_ts="${_v}" ;;
    esac
  done <<< "${_vault_read}"
fi
echo "operator=${operator:-unknown}"
echo "operator_last_branch=${operator_last_branch}"
echo "operator_pointer_found=${operator_pointer_found}"
echo "operator_branch_on_origin=${operator_branch_on_origin}"
echo "operator_last_ts=${operator_last_ts}"

# Only accept origin/<branch> (reject bare "origin" from odd remote HEAD shortnames).
# Prefer newest non-integration branch; fall back to origin/master then origin/develop.
remote_last="$(
  git for-each-ref refs/remotes/origin/ --sort=-committerdate \
    --format='%(refname:short)|%(committerdate:iso-strict)|%(subject)' \
    | { grep -E '^origin/[^|]+\|' || true; } \
    | { grep -vE '^origin/HEAD\||^origin/develop\||^origin/master\|' || true; } \
    | head -1
)"

if [[ -z "${remote_last}" ]]; then
  # Fall back: master, then develop, then any origin/* branch
  for _cand in origin/master origin/develop; do
    if git show-ref --verify --quiet "refs/remotes/${_cand}"; then
      remote_last="$(git for-each-ref "refs/remotes/${_cand}" --format='%(refname:short)|%(committerdate:iso-strict)|%(subject)' | head -1)"
      break
    fi
  done
fi
if [[ -z "${remote_last}" ]]; then
  remote_last="$(
    git for-each-ref refs/remotes/origin/ --sort=-committerdate \
      --format='%(refname:short)|%(committerdate:iso-strict)|%(subject)' \
      | { grep -E '^origin/[^|]+\|' || true; } \
      | { grep -vE '^origin/HEAD\|' || true; } \
      | head -1
  )"
fi

IFS='|' read -r ref date subject <<< "${remote_last}"
branch="${ref#origin/}"
# Guard: never treat remote name itself as a branch
if [[ -z "${branch}" || "${branch}" == "origin" || "${ref}" != origin/* ]]; then
  ref="origin/master"
  branch="master"
  if git show-ref --verify --quiet "refs/remotes/origin/master"; then
    date="$(git log -1 --format=%cI origin/master 2>/dev/null || true)"
    subject="$(git log -1 --format=%s origin/master 2>/dev/null || true)"
  fi
fi

echo "current=${current}"
echo "remote_last=${branch}"
echo "remote_last_date=${date}"
echo "remote_last_subject=${subject}"
echo "remote_ref=${ref}"

# Divergence vs local (if the local branch for remote_last exists)
# behind = commits on the remote not yet in local (work from other machines)
remote_last_behind=0
remote_last_ahead=0
if [[ -n "${branch}" ]] && git show-ref --verify --quiet "refs/heads/${branch}"; then
  remote_last_behind=$(git rev-list --count "${branch}..${ref}" 2>/dev/null || echo 0)
  remote_last_ahead=$(git rev-list --count "${ref}..${branch}" 2>/dev/null || echo 0)
fi
echo "remote_last_behind=${remote_last_behind}"
echo "remote_last_ahead=${remote_last_ahead}"

# Current branch sync vs upstream (what the user most wants to know)
current_behind=0
current_ahead=0
current_upstream=""
if [[ "${current}" != "unknown" ]]; then
  if current_upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || true)"; then
    :
  fi
  if [[ -z "${current_upstream}" ]] && git show-ref --verify --quiet "refs/remotes/origin/${current}"; then
    current_upstream="origin/${current}"
  fi
  if [[ -n "${current_upstream}" ]]; then
    current_behind=$(git rev-list --count "HEAD..${current_upstream}" 2>/dev/null || echo 0)
    current_ahead=$(git rev-list --count "${current_upstream}..HEAD" 2>/dev/null || echo 0)
  fi
fi

echo "current_upstream=${current_upstream:-none}"
echo "current_behind=${current_behind}"
echo "current_ahead=${current_ahead}"

if [[ "${current}" == "${branch}" ]]; then
  echo "remote_last_match=yes"
else
  echo "remote_last_match=no"
fi

# -------------------------------------------------------------------------
# Diff: current HEAD vs remote-last tip (factor into switch offer)
# vs_remote_last_behind = commits on remote-last not in current
# vs_remote_last_ahead  = commits on current not in remote-last
# -------------------------------------------------------------------------
vs_remote_last_behind=0
vs_remote_last_ahead=0
vs_remote_last_summary="n/a"
vs_remote_last_subjects=""
if [[ -n "${ref}" ]] && git rev-parse --verify --quiet "${ref}" >/dev/null 2>&1; then
  vs_remote_last_behind=$(git rev-list --count "HEAD..${ref}" 2>/dev/null || echo 0)
  vs_remote_last_ahead=$(git rev-list --count "${ref}..HEAD" 2>/dev/null || echo 0)
  if [[ "${current}" == "${branch}" ]]; then
    vs_remote_last_summary="on remote-last (${branch}); same tip as comparison base when synced"
  elif [[ "${vs_remote_last_behind}" -eq 0 && "${vs_remote_last_ahead}" -eq 0 ]]; then
    vs_remote_last_summary="current and ${branch} point at the same commit (diverged names only)"
  else
    vs_remote_last_summary="current ${current} vs ${branch}: ${vs_remote_last_behind} commit(s) only on remote-last, ${vs_remote_last_ahead} only on current"
  fi
  # Short subject samples (max 3 each side) for the switch offer
  if [[ "${vs_remote_last_behind}" -gt 0 ]]; then
    _only_remote="$(git log --oneline -3 "HEAD..${ref}" 2>/dev/null | tr '\n' ';' | sed 's/;$//')"
    vs_remote_last_subjects="only_on_remote_last=${_only_remote}"
  fi
  if [[ "${vs_remote_last_ahead}" -gt 0 ]]; then
    _only_current="$(git log --oneline -3 "${ref}..HEAD" 2>/dev/null | tr '\n' ';' | sed 's/;$//')"
    if [[ -n "${vs_remote_last_subjects}" ]]; then
      vs_remote_last_subjects="${vs_remote_last_subjects}|only_on_current=${_only_current}"
    else
      vs_remote_last_subjects="only_on_current=${_only_current}"
    fi
  fi
fi
echo "vs_remote_last_behind=${vs_remote_last_behind}"
echo "vs_remote_last_ahead=${vs_remote_last_ahead}"
echo "vs_remote_last_summary=${vs_remote_last_summary}"
echo "vs_remote_last_subjects=${vs_remote_last_subjects}"

# -------------------------------------------------------------------------
# Integration branch (develop preferred, else master/main) vs origin
# Offer ff-only update when local integration is behind and clean-ff-able
# -------------------------------------------------------------------------
integration_branch=""
integration_remote_ref=""
for _ib in develop master main; do
  if git show-ref --verify --quiet "refs/remotes/origin/${_ib}"; then
    integration_branch="${_ib}"
    integration_remote_ref="origin/${_ib}"
    break
  fi
done

integration_local_exists=no
integration_behind=0
integration_ahead=0
integration_ff_offer=no
integration_offer_message=""
if [[ -n "${integration_branch}" ]]; then
  if git show-ref --verify --quiet "refs/heads/${integration_branch}"; then
    integration_local_exists=yes
    integration_behind=$(git rev-list --count "${integration_branch}..${integration_remote_ref}" 2>/dev/null || echo 0)
    integration_ahead=$(git rev-list --count "${integration_remote_ref}..${integration_branch}" 2>/dev/null || echo 0)
  else
    # No local ref — treat as fully behind remote tip count from empty merge-base heuristic
    integration_behind=$(git rev-list --count "${integration_remote_ref}" 2>/dev/null || echo 0)
    integration_ahead=0
  fi

  if [[ "${integration_behind}" -gt 0 && "${integration_ahead}" -eq 0 ]]; then
    integration_ff_offer=yes
    if [[ "${integration_local_exists}" == "yes" ]]; then
      integration_offer_message="Local ${integration_branch} is behind ${integration_remote_ref} by ${integration_behind} commit(s) — offer: git fetch origin ${integration_branch}:${integration_branch} (ff-only, no checkout) or checkout + git pull --ff-only"
    else
      integration_offer_message="No local ${integration_branch}; remote has tip at ${integration_remote_ref} — offer: git branch ${integration_branch} ${integration_remote_ref} (track) or checkout -b ${integration_branch} --track ${integration_remote_ref}"
    fi
  elif [[ "${integration_behind}" -gt 0 && "${integration_ahead}" -gt 0 ]]; then
    integration_offer_message="Local ${integration_branch} diverged from ${integration_remote_ref} (${integration_behind} behind, ${integration_ahead} ahead) — do not auto-ff; offer explicit rebase/merge"
  elif [[ "${integration_behind}" -eq 0 && "${integration_ahead}" -gt 0 ]]; then
    integration_offer_message="Local ${integration_branch} is ahead of ${integration_remote_ref} by ${integration_ahead} (unpushed)"
  elif [[ -n "${integration_branch}" ]]; then
    integration_offer_message="Local ${integration_branch} matches ${integration_remote_ref}"
  fi
fi

echo "integration_branch=${integration_branch}"
echo "integration_remote_ref=${integration_remote_ref}"
echo "integration_local_exists=${integration_local_exists}"
echo "integration_behind=${integration_behind}"
echo "integration_ahead=${integration_ahead}"
echo "integration_ff_offer=${integration_ff_offer}"
echo "integration_offer_message=${integration_offer_message}"

# Switch policy: session-start always targets remote_last (--apply performs it).
switch_offer=no
if [[ "${current}" != "${branch}" && -n "${branch}" ]]; then
  switch_offer=yes
fi
echo "switch_offer=${switch_offer}"
echo "switch_policy=auto_remote_last"

porcelain="$(git status --porcelain 2>/dev/null || true)"

# Soft-dirty: session spin-up artifacts only — safe to restore before switch
# (envelope rewrites context-latest; security sweep is regenerated).
_soft_dirty_only=no
_soft_paths=()
if [[ -n "${porcelain}" ]]; then
  _soft_dirty_only=yes
  while IFS= read -r _pline; do
    [[ -z "${_pline}" ]] && continue
    _ppath="${_pline:3}"
    # rename "old -> new"
    if [[ "${_ppath}" == *" -> "* ]]; then
      _ppath="${_ppath##* -> }"
    fi
    _ppath="${_ppath//\"/}"
    if [[ "${_ppath}" == "reports/sessions/context-latest.json" \
       || "${_ppath}" == "reports/sessions/context-latest.txt" \
       || "${_ppath}" == reports/security/session-sweep-*.md ]]; then
      _soft_paths+=("${_ppath}")
    else
      _soft_dirty_only=no
    fi
  done <<< "${porcelain}"
fi
echo "soft_dirty_only=${_soft_dirty_only}"

# -------------------------------------------------------------------------
# --apply: fetch already done → switch remote_last → pull (session-start order)
# -------------------------------------------------------------------------
switch_applied=no
switch_result=none
switch_error=""
if [[ "${APPLY}" -eq 1 ]]; then
  # Soft-dirty session noise: restore so team-tip switch is not blocked
  if [[ -n "${porcelain}" && "${_soft_dirty_only}" == "yes" ]]; then
    for _sp in "${_soft_paths[@]+"${_soft_paths[@]}"}"; do
      if [[ -n "${_sp}" ]] && git ls-files --error-unmatch "${_sp}" >/dev/null 2>&1; then
        git restore --worktree --staged -- "${_sp}" 2>/dev/null || git checkout -- "${_sp}" 2>/dev/null || true
      elif [[ -n "${_sp}" && -e "${_sp}" ]]; then
        rm -f "${_sp}" 2>/dev/null || true
      fi
    done
    porcelain="$(git status --porcelain 2>/dev/null || true)"
  fi

  if [[ -z "${branch}" ]]; then
    switch_result=no_remote_last
    switch_error="No remote_last branch resolved after fetch"
  elif [[ -n "${porcelain}" ]]; then
    # Real WIP — never auto-switch (FORCE_DIRTY does not override)
    switch_result=blocked_dirty
    switch_error="Working tree dirty on ${current} — commit/stash before auto-switch to ${branch}"
  elif [[ "${current}" == "${branch}" ]]; then
    # Already on team tip: ff-only pull when behind
    if [[ "${current_behind}" -gt 0 ]]; then
      if git pull --ff-only 2>/dev/null; then
        switch_applied=yes
        switch_result=pulled
      else
        switch_result=pull_failed
        switch_error="git pull --ff-only failed on ${branch}"
      fi
    else
      switch_applied=yes
      switch_result=already_on
    fi
  else
    # Switch to remote_last (team tip), then pull
    _checkout_ok=0
    if git show-ref --verify --quiet "refs/heads/${branch}"; then
      if git checkout "${branch}" 2>/dev/null; then
        _checkout_ok=1
      fi
    elif git show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
      # Prefer create -b (never -B reset — would drop unpushed local commits if ref reappears)
      if git checkout -b "${branch}" --track "origin/${branch}" 2>/dev/null \
        || git checkout -b "${branch}" "origin/${branch}" 2>/dev/null \
        || git checkout --track "origin/${branch}" 2>/dev/null; then
        _checkout_ok=1
      fi
    fi
    if [[ "${_checkout_ok}" -eq 1 ]]; then
      current="$(git branch --show-current 2>/dev/null || echo unknown)"
      current_upstream=""
      if current_upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || true)"; then
        :
      fi
      if [[ -z "${current_upstream}" ]] && git show-ref --verify --quiet "refs/remotes/origin/${current}"; then
        current_upstream="origin/${current}"
      fi
      _pull_ok=1
      if [[ -n "${current_upstream}" ]]; then
        current_behind=$(git rev-list --count "HEAD..${current_upstream}" 2>/dev/null || echo 0)
        current_ahead=$(git rev-list --count "${current_upstream}..HEAD" 2>/dev/null || echo 0)
        if [[ "${current_behind}" -gt 0 ]]; then
          if ! git pull --ff-only 2>/dev/null; then
            _pull_ok=0
          fi
          current_behind=$(git rev-list --count "HEAD..${current_upstream}" 2>/dev/null || echo 0)
          current_ahead=$(git rev-list --count "${current_upstream}..HEAD" 2>/dev/null || echo 0)
        fi
      fi
      switch_applied=yes
      if [[ "${_pull_ok}" -eq 1 ]]; then
        switch_result=switched
      else
        switch_result=switched_pull_failed
        switch_error="Checked out ${branch} but git pull --ff-only failed (diverged or network)"
      fi
      porcelain="$(git status --porcelain 2>/dev/null || true)"
      if [[ "${current}" == "${branch}" ]]; then
        remote_last_match=yes
        switch_offer=no
      fi
      # remote_last is switch authority; vault pointer is secondary
      if [[ -n "${current}" && "${current}" != "unknown" ]]; then
        python3 "$(dirname "$0")/vault-workspace-pointer.py" \
          --emit --branch "${current}" \
          --source "resume-branch-apply" 2>/dev/null || true
        operator_last_branch="${current}"
        operator_pointer_found=yes
      fi
    else
      switch_result=checkout_failed
      switch_error="Could not checkout ${branch} (missing local/remote ref?)"
    fi
  fi
fi

echo "switch_applied=${switch_applied}"
echo "switch_result=${switch_result}"
if [[ -n "${switch_error}" ]]; then
  echo "switch_error=${switch_error}"
fi
# Re-emit current after possible switch so consumers see post-apply state
echo "current=${current}"
echo "current_upstream=${current_upstream:-none}"
echo "current_behind=${current_behind}"
echo "current_ahead=${current_ahead}"
echo "remote_last_match=$([[ "${current}" == "${branch}" ]] && echo yes || echo no)"
echo "switch_offer=$([[ "${current}" != "${branch}" && -n "${branch}" ]] && echo yes || echo no)"

if [[ -n "${porcelain}" ]]; then
  working_tree="dirty"
  sync_status="dirty"
  if [[ "${switch_result}" == "blocked_dirty" ]]; then
    sync_message="Working tree dirty on ${current} — blocked auto-switch to remote_last=${branch}."
  else
    sync_message="Working tree has uncommitted changes on ${current}."
  fi
elif [[ "${current}" == "unknown" ]]; then
  working_tree="clean"
  sync_status="unknown"
  sync_message="Detached or unknown branch — cannot confirm sync."
elif [[ -z "${current_upstream}" ]]; then
  working_tree="clean"
  sync_status="no_upstream"
  sync_message="No upstream for ${current} — cannot confirm you are up to date."
elif [[ "${current_behind}" -eq 0 && "${current_ahead}" -eq 0 ]]; then
  working_tree="clean"
  sync_status="up_to_date"
  if [[ "${current}" == "${branch}" ]]; then
    sync_message="You are up to date on ${current} (latest remote activity)."
  elif [[ "${operator_pointer_found}" == "yes" && -n "${operator_last_branch}" && "${current}" == "${operator_last_branch}" ]]; then
    sync_message="You are up to date on your last branch (${current}). Latest remote activity is on ${branch}."
  else
    sync_message="You are up to date on ${current}. Latest remote activity is on ${branch}."
  fi
elif [[ "${current_behind}" -gt 0 && "${current_ahead}" -eq 0 ]]; then
  working_tree="clean"
  sync_status="behind"
  sync_message="Behind ${current_upstream} by ${current_behind} commit(s) on ${current} — pull to sync."
elif [[ "${current_behind}" -eq 0 && "${current_ahead}" -gt 0 ]]; then
  working_tree="clean"
  sync_status="ahead"
  sync_message="You are up to date with remote; ${current_ahead} local commit(s) on ${current} not pushed."
else
  working_tree="clean"
  sync_status="diverged"
  sync_message="Diverged from ${current_upstream} on ${current} (${current_behind} behind, ${current_ahead} ahead)."
fi

echo "working_tree=${working_tree}"

if [[ "${operator_pointer_found}" == "yes" && -n "${operator_last_branch}" ]]; then
  if [[ "${current}" == "${operator_last_branch}" ]]; then
    echo "operator_resume_match=yes"
  else
    echo "operator_resume_match=no"
  fi
else
  echo "operator_resume_match=unknown"
fi

echo "sync_status=${sync_status}"
echo "sync_message=${sync_message}"

# -------------------------------------------------------------------------
# Alignment recommendations (when not on remote_last after apply / report)
# -------------------------------------------------------------------------
on_remote_last=no
if [[ -n "${branch}" && "${current}" == "${branch}" ]]; then
  on_remote_last=yes
fi
echo "on_remote_last=${on_remote_last}"

align_recommendations=""
if [[ "${on_remote_last}" == "yes" ]]; then
  if [[ "${current_behind}" -gt 0 ]]; then
    align_recommendations="On remote_last but behind upstream by ${current_behind} — run: git pull --ff-only"
  else
    align_recommendations="On remote_last (${branch}); team tip synced"
  fi
else
  _parts=()
  _parts+=("Not on remote_last (team tip=${branch:-none}; current=${current})")
  if [[ -n "${branch}" ]]; then
    _parts+=("Prefer: git fetch origin && git checkout ${branch} && git pull --ff-only")
  fi
  if [[ "${vs_remote_last_behind}" -gt 0 || "${vs_remote_last_ahead}" -gt 0 ]]; then
    _parts+=("Delta vs remote_last: ${vs_remote_last_behind} only-on-tip / ${vs_remote_last_ahead} only-on-current")
  fi
  if [[ "${switch_result}" == "blocked_dirty" ]]; then
    _parts+=("Blocked by dirty WIP — commit or stash before auto-switch")
  fi
  _parts+=("If staying here: treat this branch resume card as local only; re-check remote_last before merge/PR")
  if [[ "${integration_behind}" -gt 0 ]]; then
    _parts+=("Integration ${integration_branch} is ${integration_behind} behind ${integration_remote_ref}")
  fi
  align_recommendations="$(IFS='; '; echo "${_parts[*]}")"
fi
echo "align_recommendations=${align_recommendations}"