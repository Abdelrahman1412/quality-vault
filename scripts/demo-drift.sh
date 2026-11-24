#!/usr/bin/env bash
# Plant three kinds of drift in a throwaway copy of the app and show the vault catches each one.
#   1. a business rule changes      -> `qv sweep` names the module and the rules to re-read
#   2. a new enum value ships       -> `qv check` demands a data decision for it
#   3. a new function ships         -> `qv check` refuses code that no module owns
# Exits 0 only if all three are caught. Usage: scripts/demo-drift.sh [path or URL of the app]
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
source_repo="${1:-${QV_SUBJECT:-$here/../golden-seed}}"
qv="${QV:-qv}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git clone -q "$source_repo" "$work/app"
watermark="$(sed -n 's/^subject_sha: *//p' "$here/vault/05-Release-Maintenance/watermark.yaml")"
git -C "$work/app" checkout -q "$watermark"
git -C "$work/app" -c user.name=demo -c user.email=demo@example.com switch -q -c drift

run() { (cd "$here" && "$qv" --subject "$work/app" "$@"); }
caught=0

echo "== 1. A rule changes: leave may now start before the hire date"
python3 - "$work/app/src/golden_seed/hrapp/services.py" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text()
old = '    if start < emp.hire_date:\n        raise ServiceError("leave starts before the hire date")\n'
assert old in s, "the demo expects the hire-date rule in request_leave"
p.write_text(s.replace(old, ""))
PY
git -C "$work/app" -c user.name=demo -c user.email=demo@example.com commit -qam "allow leave before hire"
if out="$(run sweep)"; then
  echo "NOT CAUGHT: sweep reported nothing"
else
  echo "$out" | sed -n '/^leave:/,/^$/p'
  grep -q "services.request_leave" <<<"$out" && grep -q "LV-R03" <<<"$out" && caught=$((caught + 1))
fi

echo
echo "== 2. A new enum value ships: LeaveKind.PARENTAL"
sed -i 's/    UNPAID = "UNPAID"/    UNPAID = "UNPAID"\n    PARENTAL = "PARENTAL"/' \
  "$work/app/src/golden_seed/hrapp/models.py"
if out="$(run check)"; then
  echo "NOT CAUGHT: check passed"
else
  grep "Q032" <<<"$out" && grep -q "LeaveKind.PARENTAL" <<<"$out" && caught=$((caught + 1))
fi
git -C "$work/app" checkout -q -- .

echo
echo "== 3. A new function ships with no module: services.transfer_employee"
cat >>"$work/app/src/golden_seed/hrapp/services.py" <<'PY'


def transfer_employee(s, emp, department):
    emp.department = department
    return emp
PY
if out="$(run check)"; then
  echo "NOT CAUGHT: check passed"
else
  grep "Q010" <<<"$out" && grep -q "services.transfer_employee" <<<"$out" && caught=$((caught + 1))
fi

echo
echo "Caught $caught of 3 planted drifts."
[ "$caught" -eq 3 ]
