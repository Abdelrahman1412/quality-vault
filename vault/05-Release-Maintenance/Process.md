# Release maintenance

Run this after every release of the app. It keeps the vault describing the code that ships, so
nobody has to explore the app again to find out what changed.

## Steps

1. **Triage the findings register first.** Run `qv finding reverify`. An open finding whose
   command now passes is closed (`fixed` or `stale`). Do this first, because an open R1 finding
   means the green checks below may be lying.
2. **Sweep.** `qv sweep --until <release tag or sha>` lists every function and class that was
   added, removed or changed since the watermark, grouped by module, with the rules that cite
   each one.
3. **Review each flagged module, in dependency order** (see the
   [mind map](../01-System-Map/Mind-Map.md)): organisation → leave → offboarding → payroll →
   notifications. For each one:
   - **spec:** add new rules with the next free id, retire the ones that stopped applying (never
     delete or renumber), and add a dated changelog line naming the commits;
   - **test cases:** one case per new rule at the lowest layer that proves it, and point
     "Automated by" at the test if one landed with the release;
   - **data inventory:** a new enum value or state needs a row: seeded, `gap` or `limit`.
4. **Give new code an owner.** A symbol the sweep lists under "NO MODULE" goes into a module in
   `vault.yaml`.
5. **Check and regenerate.** `qv lock`, `qv generate`, then `qv check` must pass.
6. **Advance the watermark.** `qv sweep --advance --reviewed <modules> --note "<one line>"`.
   It refuses if you skip a module the sweep flagged, and it appends a row to the
   [run log](Run-Log.md).
7. **Log what you found.** Anything surprising along the way (a rule with no test, a seed gap, a
   spec that was wrong) goes into the findings register with `qv finding add`.

## What runs automatically

| When | What | Fails when |
|---|---|---|
| every push and pull request | `qv check` against the release in the watermark | the vault contradicts the code it claims to describe |
| nightly | `qv sweep` and `qv check` against the app's `main` | the app has moved on and the vault has not caught up |

The nightly failure is the reminder to run this process.
