# Organisation: test cases

Each case proves one or more rules from the [spec](../02-Modules/organisation/Behavior-Spec.md), at
the lowest layer that can prove it. "Automated by" names a real test (`file::name`) or a seed
contract state (`contract:<id>`); `qv check` fails if it does not exist. A dash means nobody has
automated it yet; the [dashboard](../00-Home/Dashboard.md) lists those.

| ID | Rules | Layer | Case | Automated by | Why this layer |
|---|---|---|---|---|---|
| ORG-TC01 | ORG-R01 | service | Create department ENG, then ENG again: the second is refused and one row exists. | — | |
| ORG-TC02 | ORG-R02 | service | Create role Manager twice: the second is refused. | — | |
| ORG-TC03 | ORG-R03 | service | Create a role with only `leave:approve`: its scopes are `leave:approve self:read`. | — | |
| ORG-TC04 | ORG-R03 | contract | Every seeded role carries the baseline scope. | `contract:roles/baseline-scope` | |
| ORG-TC05 | ORG-R04 | service | Hire with salary 0 and with −1: both refused; salary 1 accepted (boundary). | — | |
| ORG-TC06 | ORG-R05 | service | Hire the same email twice: the second is refused, even in another department. | — | |
| ORG-TC07 | ORG-R06 | service | Terminate a manager in the past, then hire someone under them: refused. | — | |
| ORG-TC08 | ORG-R07 | contract | Every seeded hire has a welcome message in the outbox. | `contract:mail/welcome-in-outbox` | |
| ORG-TC09 | ORG-R07 | service | A new hire's status is ACTIVE and no termination date is set. | — | |
