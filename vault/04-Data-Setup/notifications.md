# Notifications: data inventory

Every value each variable can take, and where the demo data holds it. Seed state values are
explained in the [organisation inventory](organisation.md). The outbox is a table: open it to
read every message the seed "sent".

| Variable | Value | Seed state | Notes |
|---|---|---|---|
| Message | welcome | `mail/welcome-in-outbox` | One per employee, subject "Welcome aboard". |
| Message | leave approved or declined | `gap` | The seed sends them (every decision goes through the service), but no contract state asserts it. See TF-006. |
| Message | payslip ready | `gap` | Sent for both PAID runs, but no contract state asserts it. See TF-006. |
| Mailer | SMTP during seeding | `limit` | Refused by the seed's mail guard (NTF-R02). Proven by NTF-TC02 and NTF-TC03. |
