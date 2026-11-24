---
module: notifications
prefix: NTF
summary: Every email the product sends, and how test data never sends one.
---

# Notifications: behaviour spec

The product sends email through a `Mailer`. In production that is SMTP; in tests and seeding it
is the outbox table, so nothing leaves the database.

**Read with:** [test cases](../../03-Test-Cases/notifications.md) ·
[data inventory](../../04-Data-Setup/notifications.md) · [code map](../../01-System-Map/Code-Map.md#notifications)

## Rules

| ID | Rule | Code | Since |
|---|---|---|---|
| NTF-R01 | Every message goes through a `Mailer`. The outbox mailer stores it in the outbox table and sends nothing. | `mail.Mailer`, `mail.OutboxMailer`, `models.OutboxMessage` | v0.1 |
| NTF-R02 | The SMTP mailer is the production path. Seeding must never reach it, and fails if it does. | `mail.SmtpMailer` | v0.1 |
| NTF-R03 | The product emails on three events only: hire (welcome), leave decision (approved or declined) and payment (payslip ready). Cancelling leave and terminating send nothing. | `services.hire_employee`, `services.approve_leave`, `services.reject_leave`, `services.mark_paid` | v0.1 |

## Open questions

None.

## Changelog

- 2026-11-22: spec written from the code at `cf68fa4`.
