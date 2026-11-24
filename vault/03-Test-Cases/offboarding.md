# Offboarding: test cases

Each case proves one or more rules from the [spec](../02-Modules/offboarding/Behavior-Spec.md), at
the lowest layer that can prove it. "Automated by" names a real test or a seed contract state;
`qv check` fails if it does not exist.

| ID | Rules | Layer | Case | Automated by | Why this layer |
|---|---|---|---|---|---|
| OFF-TC01 | OFF-R01 | service | Terminate a leaver again: refused. | — | |
| OFF-TC02 | OFF-R02 | service | Last day the day before the hire date: refused; on the hire date: accepted. | — | |
| OFF-TC03 | OFF-R03 | service | Terminate a manager with one current report: refused. Reassign the report, then terminate: accepted. | — | |
| OFF-TC04 | OFF-R04 | property | Leave straddling the last day is never deducted from a payslip for days after it. The thorough profile fails at once with OFF-R04's check removed. | `tests/test_properties.py::test_unpaid_days_never_exceed_the_days_worked_in_the_period` | |
| OFF-TC05 | OFF-R04 | service | Approved leave 10–14, last day 12: refused, and the message names the leave. Last day 14: accepted. | — | |
| OFF-TC06 | OFF-R05 | contract | A seeded leaver left before the anchor; someone serving notice has a last day inside the DRAFT run. | `contract:offboarding/leaver`, `contract:offboarding/notice-in-draft-period` | |
| OFF-TC07 | OFF-R05 | service | Last day yesterday: LEAVER. Last day today: NOTICE (boundary). | — | |
| OFF-TC08 | OFF-R06, OFF-R07 | contract | No seeded leaver has live leave after their last day, or a payslip for a later period. | `contract:offboarding/leaver` | |
