#!/usr/bin/env bash
# Unified local testing harness for AOE 3 DE - A New World DLC.
#
# Runs every static / data-side check the mod has and prints a single
# pass/fail summary with counts. The same checks run in CI; this script
# is the "before you push" smoke test.
#
# Stages (skip with flags):
#   --no-content        Skip content validators (XML, XS, civ refs, decks, …)
#   --no-regression     Skip Python unittest suite
#   --no-packaged       Skip packaged-mod validator (slowest)
#   --strict-locids     Treat unresolved DisplayNameID locIDs as fatal
#   --report PATH       Write the staged report to PATH
#
# Returns 0 if everything passes, 1 otherwise.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

run_content=1
run_regression=1
run_packaged=1
strict_locids=0
report_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-content)    run_content=0 ;;
    --no-regression) run_regression=0 ;;
    --no-packaged)   run_packaged=0 ;;
    --strict-locids) strict_locids=1 ;;
    --report)        shift; report_path="$1" ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# //; s/^#//'
      exit 0
      ;;
    *)
      echo "unknown flag: $1" >&2
      exit 2
      ;;
  esac
  shift
done

echo "━━━ AOE3 DE A New World DLC — local test harness ━━━"
echo "repo: $REPO_ROOT"
echo

stages=()
[[ $run_content -eq 1 ]]    && stages+=(--stage content)
[[ $run_regression -eq 1 ]] && stages+=(--stage regression)
[[ $run_packaged -eq 1 ]]   && stages+=(--stage packaged)

if [[ ${#stages[@]} -eq 0 ]]; then
  echo "no stages selected — exiting."
  exit 0
fi

extra=()
[[ $strict_locids -eq 1 ]]   && extra+=(--strict-display-name-ids)
[[ -n "$report_path" ]]      && extra+=(--report-file "$report_path")

python3 -m tools.validation.run_staged_validation "${stages[@]}" "${extra[@]}"
status=$?

echo
if [[ $status -eq 0 ]]; then
  echo "✅ All selected stages passed."
  echo
  echo "Mod inventory:"
  printf "  base civs:        %s homecity files\n" "$(ls data/homecity*.xml 2>/dev/null | wc -l)"
  printf "  revolution civs:  %s homecity files\n" "$(ls data/rvltmodhomecity*.xml 2>/dev/null | wc -l)"
  printf "  leader XS files:  %s\n" "$(find game/ai/leaders -name 'leader_*.xs' 2>/dev/null | wc -l)"
  printf "  workflows:        %s GitHub Actions checks\n" "$(ls .github/workflows/*.yml 2>/dev/null | wc -l)"
  printf "  validators:       %s static checks\n" "$(ls tools/validation/validate_*.py 2>/dev/null | wc -l)"
else
  echo "❌ One or more stages failed (exit status $status). Scroll up for details."
fi

exit $status
