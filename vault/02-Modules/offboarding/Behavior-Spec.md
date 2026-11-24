---
module: offboarding
prefix: OFF
summary: Ending employment, now or on a future last day.
---

# Offboarding: behaviour spec

Terminating sets a last working day. A last day in the past makes the person a LEAVER at once;
a last day today or later puts them on NOTICE until then.

**Read with:** [test cases](../../03-Test-Cases/offboarding.md) ·
[data inventory](../../04-Data-Setup/offboarding.md) · [code map](../../01-System-Map/Code-Map.md#offboarding)

## Rules

| ID | Rule | Code | Since |
|---|---|---|---|
| OFF-R01 | Someone who has already left cannot be terminated again. | `services.terminate_employee` | v0.1 |
| OFF-R02 | The last day cannot be before the hire date. | `services.terminate_employee` | v0.1 |
| OFF-R03 | A manager with current reports cannot be terminated until they are reassigned. | `services.terminate_employee` | v0.1 |
| OFF-R04 | Termination is refused while a live leave starts on or before the last day and ends after it. Shorten or cancel that leave first. | `services.terminate_employee` | `2e222db` |
| OFF-R05 | A last day before today makes the person a LEAVER; today or later puts them on NOTICE. | `services.terminate_employee` | v0.1 |
| OFF-R06 | Live leave that starts after the last day is cancelled automatically. | `services.terminate_employee` | v0.1 |
| OFF-R07 | A leaver gets no payslip for a period that starts after their last day. | `services.terminate_employee`, `services.start_processing` | v0.1 |

## Open questions

None.

## Changelog

- 2026-11-24: release sweep `cf68fa4..e3e619d`. Added OFF-R04 (fixed in `2e222db`, see TF-003).
- 2026-11-22: spec written from the code at `cf68fa4`.
