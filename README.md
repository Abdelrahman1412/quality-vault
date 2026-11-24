# quality-vault

**One source of truth about an app, which fails its own CI when it stops being true.**

Every testing task starts with the same questions. What does this module do? Which rules does it
enforce? Where are they tested, and at which layer? What data do I need to test it, and does it
exist? Did this break before? Without a written answer, every person and every AI agent
re-explores the code to find out. They spend the time again, and they guess where the code is
unclear.

A quality vault writes those answers down once: a mind map, behaviour specs per module, test cases
placed at the right layer, data inventories that drive a seed, and a register of past findings.
Documentation like this usually rots within a release. This repo adds `qv`, a checker that holds
every claim in the vault to the code, so the vault fails CI the moment it drifts.

| Before | After |
|---|---|
| Each task starts by reading the code again. | Each task starts from the module's spec, test cases and data. |
| Specs describe functions that were renamed months ago. | A rule that cites missing code fails `qv check`. |
| Agents fill gaps with plausible guesses. | Agents read cited facts with file and line, and fix the vault when it's wrong. |
| A new status ships and nobody seeds it. | A new enum value fails the check until someone decides its data. |
| After a release, nobody knows which docs are stale. | `qv sweep` lists every changed function, by module, with the rules to re-read. |
| The same bug is reported three times in three places. | One register, duplicates refused, every open row re-checkable. |

The worked example describes the HR app in
[golden-seed](https://github.com/Abdelrahman1412/golden-seed) (organisation, leave, payroll,
offboarding, notifications). Its seed is the demo data this vault's inventories point at.

## What is in the vault

```
vault/
  00-Home/                 Start-Here (for people and agents), Dashboard (generated)
  01-System-Map/           Mind map, architecture and stack, Code map (generated: symbol -> file:line)
  02-Modules/<module>/     Behaviour spec: numbered rules, each citing the code that enforces it
  03-Test-Cases/           Cases per rule, each at a layer, each pointing at its automation
  04-Data-Setup/           Every value of every variable, and the seeded record that holds it
  05-Release-Maintenance/  The process, the watermark, the run log
  06-Findings/             The findings register
```

Start with [Start-Here](vault/00-Home/Start-Here.md), the [mind map](vault/01-System-Map/Mind-Map.md)
or the [dashboard](vault/00-Home/Dashboard.md).

**One rule, traced through the vault:**

| Part | LV-R03: leave cannot start before the hire date |
|---|---|
| Spec | Cites `services.request_leave`, the code that enforces it. |
| Test cases | LV-TC03 at the property layer, automated by `tests/test_properties.py::test_unpaid_days_never_exceed_the_days_worked_in_the_period`. LV-TC04 at the service layer, not automated yet, so the dashboard lists it. |
| Data | "Leave starting before the hire date" is a `limit`: the product refuses it, so it is tested, not seeded. |
| Finding | TF-001 records how property tests found the bug that led to this rule. |
| Release | The sweep from `cf68fa4` to `e3e619d` flagged `request_leave`; the rule was added and the run logged. |

## What `qv check` holds the vault to

| Check | Fails when |
|---|---|
| Q004 | A rule cites a function or class that does not exist. |
| Q006, Q007 | A rule id disappears (ids are retired, never deleted or renumbered), or a new one is not locked. |
| Q010, Q011 | Code exists that no module owns, or a module claims code that is gone. |
| Q021, Q025 | A test case cites an unknown rule, or a rule has no test case. |
| Q022, Q023 | A test case has an unknown layer, or sits at `api` or `e2e` without saying why a lower layer can't prove it. |
| Q024 | "Automated by" names a test or seed state that does not exist. |
| Q030, Q031 | A data value cites an unknown seed state, or is a `gap` or `limit` with no reason. |
| Q032, Q033 | An enum value in the code is in no inventory, or an inventory lists a value the code dropped. |
| Q040 to Q044 | A finding has a bad or duplicate id, a duplicate signature, an empty field, or is open with no re-verify command. |
| Q050 | A module is missing from the mind map. |
| Q060 | The dashboard or code map is out of date. |

The checks read the code with Python's `ast`, the tests by name, and the seed's own state
contract, so the vault never has to trust itself. CI also plants three drifts in a copy of the
app (a changed rule, a new enum value, a new function) and fails unless all three are caught.

## Release maintenance

After a release, `qv sweep` compares every function and class at the watermark with the new
release. This is the real sweep that brought this vault up to date:

```
$ qv sweep
The vault describes cf68fa4; the app is at e3e619d (3 commit(s)).

  e3e619d 2026-11-23 Add property-based tests for payroll and leave invariants
  2e222db 2026-11-23 Refuse to terminate someone whose leave runs past the last day
  44d688b 2026-11-22 Fix two leave rules that property-based tests exposed

leave:
  changed  models.LeaveRequest  (src/golden_seed/hrapp/models.py:92)  rules to re-read: LV-R06, LV-R13
  changed  services.request_leave  (src/golden_seed/hrapp/services.py:144)  rules to re-read: LV-R01, ...

offboarding:
  changed  services.terminate_employee  (src/golden_seed/hrapp/services.py:100)  rules to re-read: OFF-R01, ...

Review the specs, test cases and data inventories of: leave, offboarding
then run: qv sweep --advance --reviewed leave,offboarding
```

The sweep works per symbol, not per file, because one `services.py` holds five modules. The
watermark only moves when every flagged module has been reviewed, and each move adds a row to the
[run log](vault/05-Release-Maintenance/Run-Log.md). A nightly job runs the sweep against the
app's `main`, so a release nobody absorbed turns CI red. The full process is in
[Process.md](vault/05-Release-Maintenance/Process.md).

## The findings register

Mistakes and test findings go in [one table](vault/06-Findings/Register.md), ranked by how much
they hide (R1 hides other failures; R4 is cosmetic). `qv finding add` refuses a finding whose
signature exists or whose title is too close to an existing one, and names that row, so evidence
piles up on one finding instead of spreading over copies. Every open row carries a command that
fails while the finding is true. `qv finding reverify` runs them all, so a finding that quietly
went away gets closed instead of lingering.

## Quick start

```bash
git clone https://github.com/Abdelrahman1412/golden-seed
git clone https://github.com/Abdelrahman1412/quality-vault && cd quality-vault
pip install -e '.[dev]'
qv check && qv sweep
scripts/demo-drift.sh   # plants three drifts in a copy of the app; all three are caught
```

## Commands

| Command | Does |
|---|---|
| `qv check [--warnings]` | Runs every check above. Exit 1 on any error. |
| `qv generate` | Rewrites the generated part of the dashboard and code map. Text outside the markers is kept. |
| `qv lock` | Records newly issued rule ids. |
| `qv sweep [--until REV]` | Lists what changed since the watermark. Exit 1 when behind. |
| `qv sweep --advance --reviewed a,b --note "..."` | Moves the watermark after a full review and logs the run. |
| `qv finding add --area --title --signature --rank --reverify` | Adds a finding, refusing duplicates. |
| `qv finding reverify` | Runs every open finding's command in the app's checkout. |

## Configuration reference

Everything lives in [`vault.yaml`](vault.yaml).

| Key | Meaning |
|---|---|
| `project` | Name of the app. |
| `vault_dir` | Folder holding the Markdown vault. |
| `subject.path` | Checkout of the app, relative to `vault.yaml`. |
| `subject.env_var` | Env var that overrides `path` (CI sets `QV_SUBJECT`). |
| `subject.scan` | Globs of product code the vault must cover. Every top-level function and class found needs an owner. |
| `subject.tests` | Where test references point. |
| `subject.seed_contract` | The seed's state contract. Data inventories cite its state ids and `enum/<column>` entries. Omit it if you have no seed. |
| `test_layers.order` | Test layers, lowest first. |
| `test_layers.justify_from` | Cases at this layer or above must explain why a lower layer can't prove them. |
| `modules.<name>.prefix` | Id prefix: rules are `<prefix>-R01`, test cases `<prefix>-TC01`. Quote it: YAML reads a bare `OFF` as `false`. |
| `modules.<name>.symbols` | The code the module owns, as `<file stem>.<name>`. |
| `ignore` | Symbols with no behaviour (base classes, helpers), each with a reason. |

**To adopt it for your app:** point `subject` at your repo and run `qv check`; Q010 lists every
symbol that needs a module. Group them into modules in `vault.yaml`, write one spec per module,
then run `qv lock` and `qv generate`. The checker reads Python today; `subject.py` is the one file
to change for another language.

## How it was used in practice

At an HR and payroll SaaS in the Gulf, quality started from nothing: no QA function, no frontend
tests, no seed data and no written behaviour. The vault became the place every piece of quality
work started and ended:

- **Behaviour specs per module** across the backend services and the frontend. Developers, QA and
  AI agents read the spec before the code. The standing rule: a wrong spec is fixed in the same
  pull request that finds it.
- **Test cases placed by layer** decided what got automated, and where: unit and API first,
  end-to-end only for journeys nothing lower could prove.
- **Data inventories** became the contract for a one-command seed holding every state of every
  module, used for demos, manual testing and the automated suites. A status nobody had seeded
  showed up as a gap in the inventory, not as a blocked tester.
- **The release sweep** ran after each release and updated specs, test cases, seed coverage and
  the customer help articles generated from the specs.
- **The findings register** collected test findings tripped over during unrelated work, ranked by
  what they hid. Re-verifying open rows before each sweep closed the ones that had gone away.

The checker in this repo is what that process lacked at first. The vault was kept current by
discipline, and drift between sweeps went unnoticed until someone relied on a stale page.

## Lessons

- **Cite, don't describe.** A sentence about the code can go stale unnoticed. A citation of a
  symbol cannot, because a checker can resolve it.
- **A rejected write is not a seed gap.** "A leave that overlaps another" can never exist in
  seeded data, because the product refuses it. Marking it `limit`, with the test that proves the
  refusal, stops someone spending a day trying to seed it.
- **Sweep by symbol, not by file.** One service file held five modules; a file-level diff would
  flag all of them on every release.
- **YAML has opinions.** The first run crashed because `prefix: OFF` parsed as `false`. The config
  now refuses anything but a quoted string.

## License

MIT
