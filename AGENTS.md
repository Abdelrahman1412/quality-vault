# Instructions for AI agents

Read `vault/00-Home/Start-Here.md` before you read the app's code. The vault is the first source;
the code is the second.

- **Find code through the code map** (`vault/01-System-Map/Code-Map.md`): it gives the file and
  line of every symbol and the rules that cover it.
- **Before writing a test,** read the module's spec and test cases. Put the test at the layer the
  test case names, then point the case's "Automated by" at your test.
- **Before seeding or asking for data,** read the module's data inventory. The record you need
  probably exists already; the Notes column names it.
- **When the vault is wrong, fix it in the same change.** Then run `qv lock`, `qv generate` and
  `qv check`.
- **When you find a problem,** add it with `qv finding add`. If it says the finding exists, add
  your evidence to that row instead.
- Never delete or renumber a rule id. Retire it.
