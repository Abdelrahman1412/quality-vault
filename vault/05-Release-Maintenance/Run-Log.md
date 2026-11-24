# Release maintenance run log

One row per sweep that moved the watermark. `qv sweep --advance` writes the rows.

| Date | From | To | Commits | Modules changed | Reviewed | Note |
|---|---|---|---:|---|---|---|
| 2026-11-22 | — | `cf68fa4` | 7 | all | organisation, leave, payroll, offboarding, notifications | Vault written from the code. |
| 2026-11-24 | `cf68fa4` | `e3e619d` | 3 | leave, offboarding | leave, offboarding, payroll | Property tests found three leave and offboarding bugs; added LV-R03, LV-R13, OFF-R04. Payroll re-read because leave feeds it. |
