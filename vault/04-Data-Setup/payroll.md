# Payroll: data inventory

Every value each variable can take, and where the demo data holds it. Seed state values are
explained in the [organisation inventory](organisation.md).

| Variable | Value | Seed state | Notes |
|---|---|---|---|
| PayrollStatus | DRAFT | `payroll/draft` | Next month's run. Tomas Novak's last day falls inside it. |
| PayrollStatus | PROCESSING | `payroll/processing` | This month's run, with payslips computed. |
| PayrollStatus | PAID | `payroll/paid` | The two months before this one. |
| Payslip | with an unpaid-leave deduction | `payroll/processing-with-unpaid-leave` | Omar Haddad in this month's run: exactly one person, so the deduction is easy to find. |
| Payslip | prorated for a leaver's last month | `payroll/payslips-reconcile` | Hannah Brooks in last month's PAID run, paid to the 15th. |
| Payslip | any | `payroll/payslips-reconcile` | Every payslip matches an independent recomputation; a wrong number fails the seed. |
| Run periods | overlapping | `limit` | Refused (PAY-R02). Proven by PAY-TC02. |
| Run | with nobody in scope | `limit` | Refused (PAY-R04). Proven by PAY-TC06. |
