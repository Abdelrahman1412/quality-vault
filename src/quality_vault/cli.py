"""qv: keep a quality vault true to the app it describes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quality_vault import checks, config, findings, generate, sweep
from quality_vault import vault as vault_mod
from quality_vault.subject import Subject


def _open(args: argparse.Namespace) -> tuple[vault_mod.Vault, Subject]:
    cfg = config.load(args.config, subject_override=args.subject)
    return vault_mod.load(cfg), Subject(cfg)


def cmd_check(args: argparse.Namespace) -> int:
    v, subj = _open(args)
    problems = checks.run(v, subj)
    errors = [p for p in problems if p.severity == "error"]
    shown = problems if args.warnings else errors
    for p in shown:
        print(p.render())
    warnings = len(problems) - len(errors)
    print(
        f"\n{len(errors)} error(s), {warnings} warning(s) "
        f"across {len(v.active_rules)} rules, {len(v.test_cases)} test cases, "
        f"{len(v.data)} data values, {len(v.findings)} findings."
    )
    if warnings and not args.warnings:
        print("Run with --warnings to list the warnings.")
    return 1 if errors else 0


def cmd_generate(args: argparse.Namespace) -> int:
    v, subj = _open(args)
    written = generate.write_all(v, subj)
    for p in written:
        print(f"wrote {p.relative_to(v.cfg.root)}")
    if not written:
        print("generated pages already up to date")
    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    v, _ = _open(args)
    known = list(v.locked_ids)
    new = [r.id for r in v.rules if r.id not in known]
    if not new:
        print("lock already lists every rule id")
        return 0
    header = (
        "# Every rule id ever issued. Ids are never deleted or reused:\n"
        "# a rule that no longer applies keeps its row, with text starting 'Retired'.\n"
    )
    body = "\n".join(sorted(set(known) | set(new), key=_id_key))
    v.lock_path.write_text(header + body + "\n", encoding="utf-8")
    print(f"locked {len(new)} new id(s): {', '.join(new)}")
    return 0


def _id_key(rid: str) -> tuple[str, int]:
    prefix, _, num = rid.rpartition("-R")
    return prefix, int(num) if num.isdigit() else 0


def cmd_sweep(args: argparse.Namespace) -> int:
    v, subj = _open(args)
    report = sweep.sweep(v, subj, until=args.until)
    print(report.render())
    if not args.advance:
        return 1 if report.behind else 0
    reviewed = [m for m in (args.reviewed or "").split(",") if m]
    try:
        sweep.advance(v, subj, report, reviewed, args.note or "")
    except ValueError as e:
        print(f"\nnot advanced: {e}", file=sys.stderr)
        return 1
    print(f"\nwatermark moved to {report.until[:7]}; run log updated")
    return 0


def cmd_finding_add(args: argparse.Namespace) -> int:
    v, _ = _open(args)
    try:
        fid = findings.add(
            v,
            area=args.area,
            title=args.title,
            signature=args.signature,
            rank=args.rank,
            reverify=args.reverify,
        )
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"added {fid}")
    return 0


def cmd_reverify(args: argparse.Namespace) -> int:
    v, subj = _open(args)
    results = findings.reverify_open(v, subj)
    if not results:
        print("no open findings")
    for r in results:
        print(f"{r.finding.id} [{r.finding.rank}] {r.verdict}: {r.finding.title}")
        if r.output:
            print("    " + r.output.replace("\n", "\n    "))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qv", description=__doc__)
    p.add_argument("--config", default="vault.yaml", type=Path)
    p.add_argument("--subject", help="path to the app's checkout (overrides vault.yaml)")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="fail on every way the vault has drifted from the code")
    c.add_argument("--warnings", action="store_true", help="list warnings too")
    c.set_defaults(fn=cmd_check)

    sub.add_parser("generate", help="rewrite the dashboard and code map").set_defaults(
        fn=cmd_generate
    )
    sub.add_parser("lock", help="record newly issued rule ids").set_defaults(fn=cmd_lock)

    s = sub.add_parser("sweep", help="what changed in the app since the vault's watermark")
    s.add_argument("--until", default="HEAD", help="the release to compare against")
    s.add_argument("--advance", action="store_true", help="move the watermark after a review")
    s.add_argument("--reviewed", help="comma-separated modules you reviewed")
    s.add_argument("--note", help="one line for the run log")
    s.set_defaults(fn=cmd_sweep)

    f = sub.add_parser("finding", help="the findings register")
    fsub = f.add_subparsers(dest="finding_command", required=True)
    a = fsub.add_parser("add", help="add a finding, refusing duplicates")
    a.add_argument("--area", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--signature", required=True, help="short key, e.g. leave:request:before-hire")
    a.add_argument("--rank", required=True, choices=["R1", "R2", "R3", "R4"])
    a.add_argument("--reverify", required=True, help="command that fails while the finding holds")
    a.set_defaults(fn=cmd_finding_add)
    fsub.add_parser("reverify", help="re-run every open finding's command").set_defaults(
        fn=cmd_reverify
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (config.ConfigError, FileNotFoundError, ValueError) as e:
        print(f"qv: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
