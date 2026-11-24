# Leave: data inventory

Every value each variable can take, and where the demo data holds it. Seed state values are
explained in the [organisation inventory](organisation.md).

| Variable | Value | Seed state | Notes |
|---|---|---|---|
| LeaveStatus | PENDING | `leave/pending` | Ravi Menon (Sales): annual leave three weeks after the anchor, waiting for Victor Hale. |
| LeaveStatus | APPROVED | `leave/approved` | Omar Haddad (unpaid, this month) and Lena Fischer (two annual leaves, last month). |
| LeaveStatus | REJECTED | `leave/rejected` | Sofia Alvarez (People): annual leave next month, declined by Noor Rahman. |
| LeaveStatus | CANCELLED | `leave/cancelled` | Kenji Watanabe (Engineering): sick leave two months ago, approved then cancelled. |
| LeaveKind | ANNUAL | `enum/leave_requests.kind` | Lena Fischer, Ravi Menon, Sofia Alvarez. |
| LeaveKind | SICK | `enum/leave_requests.kind` | Kenji Watanabe only, and his is cancelled. |
| LeaveKind | UNPAID | `payroll/processing-with-unpaid-leave` | Omar Haddad, 10th to 12th of this month, deducted in the PROCESSING run. |
| Approved leaves per person | two, not overlapping | `leave/no-overlap` | Lena Fischer: 3rd–4th and 20th–21st of last month. |
| Sick leave | approved | `gap` | The only sick leave is cancelled. Seed one approved sick leave to show that sick leave is not deducted. |
| Leave | overlapping a live request | `limit` | Refused (LV-R05). Proven by LV-TC06 and LV-TC07. |
| Leave | approved by the requester | `limit` | Refused (LV-R08). Proven by LV-TC11; the verifier also rejects one (LV-TC12). |
| Leave | starting before the hire date | `limit` | Refused (LV-R03). Proven by LV-TC03 and LV-TC04. |
