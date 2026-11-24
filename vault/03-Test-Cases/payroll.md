# Payroll: test cases

Each case proves one or more rules from the [spec](../02-Modules/payroll/Behavior-Spec.md), at the
lowest layer that can prove it. "Automated by" names a real test or a seed contract state;
`qv check` fails if it does not exist.

| ID | Rules | Layer | Case | Automated by | Why this layer |
|---|---|---|---|---|---|
| PAY-TC01 | PAY-R01 | service | A period ending the day before it starts is refused. | — | |
| PAY-TC02 | PAY-R02 | service | January exists; a run for 31 Jan–28 Feb is refused (shares one day). | — | |
| PAY-TC03 | PAY-R02 | contract | Seeded runs never overlap. | `contract:payroll/periods-disjoint` | |
| PAY-TC04 | PAY-R03 | service | Mark a DRAFT run paid: refused. Process a PAID run: refused. | — | |
| PAY-TC05 | PAY-R03 | contract | Seeded data holds a run in every status. | `contract:enum/payroll_runs.status` | |
| PAY-TC06 | PAY-R04 | service | Someone hired the day after the period ends, and someone who left the day before it starts, get no payslip. A run with nobody in scope is refused. | — | |
| PAY-TC07 | PAY-R05, PAY-R06 | contract | Every seeded payslip matches an independent recomputation from salary, dates and leave. | `contract:payroll/payslips-reconcile` | |
| PAY-TC08 | PAY-R06 | property | For any leave pattern, unpaid days equal the approved unpaid calendar days inside the period, never more than the days employed. | `tests/test_properties.py::test_unpaid_days_never_exceed_the_days_worked_in_the_period` | |
| PAY-TC09 | PAY-R06 | property | Approving then cancelling unpaid leave restores the payslip exactly. | `tests/test_properties.py::test_approving_then_cancelling_leave_restores_pay_and_frees_the_dates` | |
| PAY-TC10 | PAY-R06 | contract | The current PROCESSING run has exactly one person on approved unpaid leave, and they are deducted. | `contract:payroll/processing-with-unpaid-leave` | |
| PAY-TC11 | PAY-R05, PAY-R07 | property | For any salary, dates and leave: 0 ≤ deduction ≤ gross ≤ salary, and net = gross − deduction. | `tests/test_properties.py::test_payslip_net_is_never_negative_and_equals_gross_minus_deductions` | |
| PAY-TC12 | PAY-R08 | service | Mark a run with three payslips paid: three "Your payslip is ready" messages, one per person. | — | |
| PAY-TC13 | PAY-R09 | unit | February 2028 ends on the 29th, February 2027 on the 28th, December on the 31st. | — | |
