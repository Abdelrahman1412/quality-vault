# Leave: test cases

Each case proves one or more rules from the [spec](../02-Modules/leave/Behavior-Spec.md), at the
lowest layer that can prove it. "Automated by" names a real test or a seed contract state;
`qv check` fails if it does not exist.

| ID | Rules | Layer | Case | Automated by | Why this layer |
|---|---|---|---|---|---|
| LV-TC01 | LV-R01 | service | End date one day before the start: refused. Same start and end (one day): accepted. | — | |
| LV-TC02 | LV-R02 | service | A leaver requests leave: refused. | — | |
| LV-TC03 | LV-R03 | property | For any hire date and leave dates, no unpaid day is counted before the hire date. Kept regression: hired 2 Jan, leave 1–31 Jan. | `tests/test_properties.py::test_unpaid_days_never_exceed_the_days_worked_in_the_period` | |
| LV-TC04 | LV-R03 | service | Leave starting the day before the hire date is refused; starting on the hire date is accepted (boundary). | — | |
| LV-TC05 | LV-R04 | service | Someone on notice requests leave ending the day after their last day: refused; ending on it: accepted. | — | |
| LV-TC06 | LV-R05 | property | Random sequences of request, approve, reject and cancel: live requests never overlap. | `tests/test_properties.py::LeaveLifecycle::live_requests_never_overlap` | |
| LV-TC07 | LV-R05 | service | ANNUAL 10–12 is live; SICK 12–14 is refused (shares the last day, different kind). | — | |
| LV-TC08 | LV-R05 | contract | Someone has two approved leaves in one month and they do not overlap. | `contract:leave/no-overlap` | |
| LV-TC09 | LV-R06 | contract | A seeded pending request has no approver and no decision date. | `contract:leave/pending` | |
| LV-TC10 | LV-R07, LV-R14 | property | Approving or rejecting anything but PENDING is refused; every status change is an edge of the graph. | `tests/test_properties.py::LeaveLifecycle::status_changes_follow_the_graph` | |
| LV-TC11 | LV-R08 | property | At any point in a random request/decide/cancel sequence, the requester approving their own pending request is refused. | `tests/test_properties.py::LeaveLifecycle::nobody_approves_their_own_leave` | |
| LV-TC12 | LV-R08, LV-R10 | contract | Every seeded approval was made by someone with authority who is not the requester. | `contract:leave/approved` | |
| LV-TC13 | LV-R09 | service | A manager who has left tries to decide their former report's request: refused. | — | |
| LV-TC14 | LV-R10 | service | A colleague with no `leave:approve` who is not the manager approves: refused. HR with the scope from another department: accepted. | — | |
| LV-TC15 | LV-R11 | service | Approve: approver and date are set and one "Leave approved" message is in the outbox. Same for reject with "Leave declined". | — | |
| LV-TC16 | LV-R12 | service | Cancel a REJECTED request: refused. Cancel an APPROVED one: CANCELLED, and no message is sent. | — | |
| LV-TC17 | LV-R13 | property | Approve, cancel, then request the same leave again: a new PENDING request is created. | `tests/test_properties.py::test_approving_then_cancelling_leave_restores_pay_and_frees_the_dates` | |
| LV-TC18 | LV-R15 | contract | Every leave kind appears in the seeded data. | `contract:enum/leave_requests.kind` | |
