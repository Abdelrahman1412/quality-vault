# Mind map

The whole app on one page. Start here, then open a module's spec.

```mermaid
mindmap
  root((Acme HR))
    organisation
      departments
      roles and scopes
        self:read on every role
        leave:approve
      hiring
        unique email
        positive salary
        welcome email
      org chart
        one top
        no leaver as manager
    leave
      request
        no overlap with live leave
        not before hire
        not past last day
      decide
        manager or leave:approve
        never your own
      cancel
        frees the dates
      kinds
        ANNUAL
        SICK
        UNPAID deducts pay
    payroll
      runs
        DRAFT
        PROCESSING
        PAID
        periods never overlap
      payslips
        prorated gross
        unpaid leave deduction
        net never negative
    offboarding
      last day
        past means LEAVER
        future means NOTICE
      refused while
        managing people
        leave straddles last day
      cancels later leave
    notifications
      outbox in tests and seeding
      SMTP in production
      hire, decision, payslip
```

## How the modules depend on each other

```mermaid
flowchart LR
    organisation --> leave
    organisation --> payroll
    leave -->|approved UNPAID leave| payroll
    offboarding -->|last day| payroll
    offboarding -->|cancels or blocks| leave
    organisation --> notifications
    leave --> notifications
    payroll --> notifications
```

A change in **leave** can change **payroll** numbers. A change in **offboarding** can change both.
When a sweep flags one of these modules, re-read the modules downstream of it too.
