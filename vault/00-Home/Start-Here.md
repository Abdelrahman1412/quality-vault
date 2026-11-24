# Start here

This vault is the source of truth about the Acme HR app: what it does, how it is tested, what data
exists to test it, and what went wrong before. Read it before you read the code.

## Which page answers your question

| You are about to… | Read |
|---|---|
| understand the app | [Mind map](../01-System-Map/Mind-Map.md), then [Architecture](../01-System-Map/Architecture.md) |
| find where something lives in the code | [Code map](../01-System-Map/Code-Map.md): every symbol with its file and line |
| change or test a module | its behaviour spec in [02-Modules](../02-Modules/), then its [test cases](../03-Test-Cases/) |
| need data for a demo, a manual test or an automated test | the module's [data inventory](../04-Data-Setup/): every value, and the named record that holds it |
| report a bug or a mistake | the [findings register](../06-Findings/Register.md), via `qv finding add` |
| absorb a release | the [release maintenance process](../05-Release-Maintenance/Process.md) |
| see where coverage stands | the [dashboard](Dashboard.md) |

## The rules that keep it true

1. **Cite, don't describe.** Every rule names the code that enforces it, every test case names
   the test that automates it, every data value names the seed state that holds it. `qv check`
   fails when a citation points at nothing.
2. **Never renumber.** Rule ids are issued once (`rule-ids.lock`). A rule that stops applying keeps
   its id and starts with "Retired".
3. **New code needs an owner.** Every function and class in the app belongs to a module in
   `vault.yaml`, so new code cannot ship without someone deciding which spec covers it.
4. **Every release is swept.** `qv sweep` lists what changed since the vault last caught up, by
   module and by rule. The watermark only moves once every changed module has been reviewed.
5. **One finding, one row.** The register refuses duplicates. Evidence goes on the existing row.

## For AI agents

Treat this vault as the first source, and the code as the second. Before you search the
codebase, check whether the answer is already here: the code map gives exact file and line. If
you find the vault wrong, fix the vault in the same change and run `qv check`. A gap you find
goes into the findings register, not into a chat message that nobody will see again.
