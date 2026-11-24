# Offboarding: data inventory

Every value each variable can take, and where the demo data holds it. Seed state values are
explained in the [organisation inventory](organisation.md).

| Variable | Value | Seed state | Notes |
|---|---|---|---|
| Last day | before the anchor (leaver) | `offboarding/leaver` | Hannah Brooks, 15th of last month. No payslip after, no leave after, manages nobody. |
| Last day | inside the DRAFT run (notice) | `offboarding/notice-in-draft-period` | Tomas Novak. Anchored to the run's period, so it holds on every calendar day (TF-004). |
| Last day | with live leave straddling it | `limit` | Refused (OFF-R04). Proven by OFF-TC04 and OFF-TC05. |
| Terminated person | still managing people | `limit` | Refused (OFF-R03). Proven by OFF-TC03. |
| Leave after the last day | cancelled by termination | `gap` | No seeded leaver had leave booked after their last day, so the automatic cancellation (OFF-R06) has no example to show. |
