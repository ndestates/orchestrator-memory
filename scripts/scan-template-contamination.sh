#!/usr/bin/env bash
# Template contamination scan — HARD GATE for deployed project repos.
#
# After the orchestrator template is deployed to a project and customized
# (scripts/customize-skills-for-project.py), this scan fails the build if any
# template identifiers or unresolved placeholders remain in the AI surfaces.
# Intended to run AFTER customize-skills and BEFORE git commit.
#
# Usage: bash scan-template-contamination.sh [TARGET_ROOT] [PROJECT_SLUG]
#   TARGET_ROOT   default: cwd
#   PROJECT_SLUG  default: basename of TARGET_ROOT (e.g. /home/nickd/projects/orchestrator -> orchestrator)
#
# Exit 0 = clean (or template source repo, nothing to decontaminate).
# Exit 1 = contamination found (hard gate).
set -euo pipefail

TARGET="${1:-$(pwd)}"
TARGET="$(cd "$TARGET" && pwd)"
SLUG="${2:-$(basename "$TARGET")}"

OUT_DIR="${TARGET}/reports/security"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${OUT_DIR}/contamination-${TS}.txt"
: > "$OUT"

cd "$TARGET"

# Skip the orchestrator template source repo itself: its template identifiers are
# legitimate. Detected by the deploy tooling that only ships in the source repo.
if [[ "$SLUG" == "orchestrator" && -f "scripts/deploy_grok_to_project.py" ]]; then
  echo "Template source repo ($SLUG) — nothing to decontaminate." | tee -a "$OUT"
  exit 0
fi

# Template residue patterns (case-insensitive). These must not survive in a
# customized project. Add project-specific exceptions via PROJECT_SLUG only.
patterns=(
  'ndestates/orchestrator'              # template repo slug/URL (repo masquerade)
  'Project Template'                    # template project.name placeholder
  # NOTE: the bare phrase "orchestrator template" is intentionally NOT a pattern.
  # Skills legitimately attribute their origin ("ships with the orchestrator
  # template but runs inside the target repo") — flagging it produced only false
  # positives on accurate, unscrubable portability docs. The harmful signals are
  # the repo slug, the project-name placeholder, and unresolved {placeholders}.
  '\{project_name\}'                    # unresolved placeholder
  '\{project_slug\}'
  '\{project_title\}'
  '\{slug\}'
  '\{title\}'
)

scan_dirs=()
for d in .grok .github .claude .copilot; do
  [[ -d "$d" ]] && scan_dirs+=("$d")
done

if [[ ${#scan_dirs[@]} -eq 0 ]]; then
  echo "No AI surface dirs (.grok/.github/.claude/.copilot) under $TARGET — skipping." | tee -a "$OUT"
  exit 0
fi

# Legitimate references that must NOT trip the gate:
#  - deploy-backups/deploy-reports: local deploy artifacts (never committed).
#  - orchestrator-deploy / template-decontaminate skills: the deploy tool runs
#    FROM the source repo and the decontaminate skill documents the very
#    patterns it scans for — both intrinsically name the template.
exclude_dirs=(deploy-backups deploy-reports orchestrator-deploy template-decontaminate)
exclude_files=('orchestrator-deploy*' 'template-decontaminate*')

exclude_args=()
for d in "${exclude_dirs[@]}"; do exclude_args+=("--exclude-dir=$d"); done
for f in "${exclude_files[@]}"; do exclude_args+=("--exclude=$f"); done

for pattern in "${patterns[@]}"; do
  grep -RInE \
    --include='SKILL.md' --include='*.md' --include='*.prompt.md' \
    --include='*.agent.md' --include='copilot-instructions.md' --include='CLAUDE.md' \
    "${exclude_args[@]}" \
    -e "$pattern" "${scan_dirs[@]}" >> "$OUT" || true
done

if [[ -s "$OUT" ]]; then
  HITS="$(wc -l < "$OUT" | tr -d ' ')"
  echo ""
  echo "❌ CONTAMINATION GATE FAILED — ${HITS} template residue line(s) in '${SLUG}'."
  echo "   Report: ${OUT}"
  echo "   Fix: python3 scripts/customize-skills-for-project.py --project-root '${TARGET}' --auto-profile --sync"
  echo "   Do NOT commit until clean."
  exit 1
fi

echo "✅ Clean — no template residue in '${SLUG}'. Safe to commit." | tee -a "$OUT"
