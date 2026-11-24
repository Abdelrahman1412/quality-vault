---
module: organisation
prefix: ORG
summary: Departments, roles and hiring.
---

# Organisation: behaviour spec

Departments, roles and the people in them. Hiring is the only way an employee comes to exist.

**Read with:** [test cases](../../03-Test-Cases/organisation.md) ·
[data inventory](../../04-Data-Setup/organisation.md) · [code map](../../01-System-Map/Code-Map.md#organisation)

## Rules

Each rule names the code that enforces it. `qv check` fails if that code disappears, so a rule
can never describe a function that does not exist.

| ID | Rule | Code | Since |
|---|---|---|---|
| ORG-R01 | Department codes are unique. Creating a second department with the same code is refused. | `services.create_department`, `models.Department` | v0.1 |
| ORG-R02 | Role names are unique. | `services.create_role`, `models.Role` | v0.1 |
| ORG-R03 | Every role carries the baseline scope `self:read`, whatever scopes it was created with. A role without it cannot log in. | `services.create_role` | v0.1 |
| ORG-R04 | Salary must be positive at hire. | `services.hire_employee` | v0.1 |
| ORG-R05 | An email address can belong to one employee only. | `services.hire_employee`, `models.Employee` | v0.1 |
| ORG-R06 | A leaver cannot become anyone's manager. | `services.hire_employee` | v0.1 |
| ORG-R07 | A new hire starts ACTIVE and is sent a welcome message. | `services.hire_employee`, `models.EmployeeStatus` | v0.1 |

## Open questions

None.

## Changelog

- 2026-11-22: spec written from the code at `cf68fa4`.
