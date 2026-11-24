# Findings register

Every test finding and every mistake worth not repeating, in one place, once.

**How a row works**
- **Signature** is a short key (`area:thing:symptom`). `qv finding add` refuses a finding whose
  signature already exists or whose title is too close to an existing one, and names that row.
  Add your evidence there instead of opening a copy.
- **Rank** says how much harm it does by hiding other problems:
  - **R1**: hides other failures (a check that passes on nothing, a retry that masks a flake);
  - **R2**: wrong results in a whole suite or module;
  - **R3**: one test, one rule;
  - **R4**: cosmetic or superseded.
- **Re-verify** is a command, run from the app's checkout, that **fails while the finding is
  true**. `qv finding reverify` runs every open one, so a finding nobody re-checks can't stay open
  for ever: a clean run means close it.
- Rows are never deleted. A finding that went away on its own is closed as `stale`, which is
  itself worth knowing.

| ID | Found | Area | Finding | Signature | Rank | Status | Re-verify |
|---|---|---|---|---|---|---|---|
| TF-001 | 2026-11-22 | leave | Leave could start before the hire date, so a payslip deducted days the person was not employed. The deduction clamp hid it by capping net pay at zero. | `leave:request:starts-before-hire` | R2 | fixed 2026-11-22 (`44d688b`, LV-R03) | `pytest -q tests/test_properties.py -k unpaid_days` |
| TF-002 | 2026-11-22 | leave | Requesting the same leave again after cancelling it raised a raw database error: the unique constraint ignored the request's status. | `leave:request:cancelled-holds-dates` | R3 | fixed 2026-11-22 (`44d688b`, LV-R13) | `pytest -q tests/test_properties.py -k cancelling` |
| TF-003 | 2026-11-23 | offboarding | Termination was accepted while approved leave ran past the last day, leaving leave days nobody could be paid or docked for. | `offboarding:terminate:leave-straddles-last-day` | R2 | fixed 2026-11-23 (`2e222db`, OFF-R04) | `HYPOTHESIS_PROFILE=thorough pytest -q tests/test_properties.py -k unpaid_days` |
| TF-004 | 2026-11-22 | seed | A fixture dated "anchor + N days" fell outside the payroll period it was meant to sit in on some calendar days, so the suite failed on dates, not on commits. | `seed:fixture:date-offset-decays` | R2 | fixed 2026-11-22 (anchored to the period) | `pytest -q tests/test_decaying_dates.py` |
| TF-005 | 2026-11-22 | seed | Presence checks written as "fail if a bad row exists" passed on an empty database, so a seed that wrote nothing looked healthy. | `seed:verifier:passes-on-empty-db` | R1 | fixed 2026-11-22 (witnesses required) | `pytest -q tests/test_anti_pattern.py` |
| TF-006 | 2026-11-24 | notifications | The seed sends leave-decision and payslip emails, but no contract state asserts them. A change that stopped them would pass every check. | `notifications:seed:decision-and-payslip-mail-unasserted` | R3 | open | `grep -q 'mail/payslip' golden-seed.yaml` |
| TF-007 | 2026-11-24 | organisation | No test exercises the refusal rules at the service layer one by one (duplicate email, zero salary, a leaver as manager). They are only covered indirectly, through seeding. | `organisation:tests:service-refusals-untested` | R3 | open | `test -f tests/test_services.py` |
