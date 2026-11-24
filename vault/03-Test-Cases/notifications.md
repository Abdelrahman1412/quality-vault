# Notifications: test cases

Each case proves one or more rules from the [spec](../02-Modules/notifications/Behavior-Spec.md),
at the lowest layer that can prove it. "Automated by" names a real test or a seed contract state;
`qv check` fails if it does not exist.

| ID | Rules | Layer | Case | Automated by | Why this layer |
|---|---|---|---|---|---|
| NTF-TC01 | NTF-R01 | service | A full seed leaves every message in the outbox. | `tests/test_guards.py::test_seeded_mail_stays_in_the_outbox` | |
| NTF-TC02 | NTF-R02 | service | With seeding running, any SMTP connection attempt raises. | `tests/test_guards.py::test_inert_mail_blocks_smtp` | |
| NTF-TC03 | NTF-R02 | service | A seeder wired to the SMTP mailer fails and writes nothing. | `tests/test_guards.py::test_a_seeder_wired_to_real_smtp_fails_and_writes_nothing` | |
| NTF-TC04 | NTF-R03 | contract | Every seeded hire has a welcome message. | `contract:mail/welcome-in-outbox` | |
| NTF-TC05 | NTF-R03 | service | Cancel leave and terminate someone: the outbox gains no message. | — | |
