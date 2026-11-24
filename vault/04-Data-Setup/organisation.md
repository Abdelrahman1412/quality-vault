# Organisation: data inventory

Every value each variable can take, and where the demo data holds it. One
`golden-seed seed --reset` builds all of it, so the same tenant serves a demo, a manual test
session and the automated suite.

**Seed state** is one of:
- a state id from the seed's contract (`golden-seed.yaml`), which the seed's verifier proves on
  every run;
- `enum/<table.column>`: the seed's enum coverage guarantees every value of that column exists;
- `gap`: valid, but not seeded yet. Notes say what is missing;
- `limit`: cannot be a seeded state, usually because the product refuses to write it. Test it at
  the layer named in Notes instead.

`qv check` fails on an unknown state id, and on any enum value in the code that no inventory
lists, so a new status cannot ship without a decision about its data.

| Variable | Value | Seed state | Notes |
|---|---|---|---|
| EmployeeStatus | ACTIVE | `enum/employees.status` | Most of the tenant. Daniel Osei, head of Engineering, is a good default. |
| EmployeeStatus | NOTICE | `offboarding/notice-in-draft-period` | Tomas Novak (Finance). Last day falls inside next month's DRAFT run. |
| EmployeeStatus | LEAVER | `offboarding/leaver` | Hannah Brooks (Sales). Left on the 15th of last month. |
| Role | Admin | `roles/admin-held` | Maya Lindqvist (CEO, top of the chart) and Noor Rahman (head of People). |
| Role | Manager | `org/manager-chain` | The heads of Engineering, Finance and Sales. Each manages their department. |
| Role | Employee | `org/departments-staffed` | Named fixtures plus 12 generated people, spread over four departments. |
| Position in chart | top (no manager) | `org/manager-chain` | Maya Lindqvist. Exactly one person has no manager. |
| Position in chart | manager of a leaver | `offboarding/leaver` | Victor Hale manages Hannah Brooks, who has left. |
| Manager | a leaver | `limit` | Refused at hire (ORG-R06). Proven by ORG-TC07 at the service layer. |
| Salary | zero or negative | `limit` | Refused at hire (ORG-R04). Proven by ORG-TC05. |
| Hire date | inside an open payroll period | `gap` | Everyone is hired before the oldest seeded period, so no payslip shows a prorated first month. Add one fixture hired mid-month in the PROCESSING run. |
