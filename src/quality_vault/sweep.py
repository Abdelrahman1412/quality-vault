"""Release maintenance: what changed in the app since the vault last caught up, and where.

The sweep compares every function and class at the watermark with the same
symbol at the new release. A changed symbol names its module and the rules
that cite it, so a release review starts from a list, not a re-exploration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import yaml

from quality_vault.subject import Subject
from quality_vault.vault import Vault


@dataclass(frozen=True)
class Change:
    symbol: str
    kind: str  # added | removed | changed
    module: str  # owning module, or "" when no module owns it
    rules: tuple[str, ...]
    location: str
    cited_by: tuple[str, ...] = ()  # other modules whose rules cite this symbol


@dataclass
class SweepReport:
    since: str
    until: str
    commits: list[str] = field(default_factory=list)
    changes: list[Change] = field(default_factory=list)

    @property
    def behind(self) -> bool:
        return self.since != self.until

    @property
    def stale_modules(self) -> list[str]:
        return sorted({m for c in self.changes for m in (c.module, *c.cited_by) if m})

    @property
    def unowned(self) -> list[Change]:
        return [c for c in self.changes if not c.module and c.kind != "removed"]

    def render(self) -> str:
        if not self.behind:
            return f"Up to date: the vault describes {self.until[:7]}."
        out = [
            f"The vault describes {self.since[:7]}; the app is at {self.until[:7]} "
            f"({len(self.commits)} commit(s)).",
            "",
            *[f"  {c}" for c in self.commits],
            "",
        ]
        if not self.changes:
            out.append(
                "No scanned symbol changed. Advance the watermark with `qv sweep --advance`."
            )
            return "\n".join(out)
        for module in [*self.stale_modules, ""]:
            group = [c for c in self.changes if c.module == module]
            if not group:
                continue
            out.append(f"{module or 'NO MODULE (new code with no spec)'}:")
            for c in group:
                cites = f"  rules to re-read: {', '.join(c.rules)}" if c.rules else ""
                if c.cited_by:
                    cites += f" (also cited by {', '.join(c.cited_by)})"
                out.append(f"  {c.kind:8} {c.symbol}  ({c.location}){cites}")
            out.append("")
        out.append(
            "Review the specs, test cases and data inventories of: "
            + ", ".join(self.stale_modules or ["(none)"])
        )
        out.append("then run: qv sweep --advance --reviewed " + ",".join(self.stale_modules))
        return "\n".join(out)


def sweep(v: Vault, subj: Subject, until: str = "HEAD") -> SweepReport:
    mark = v.watermark()
    if not mark.get("subject_sha"):
        raise ValueError(f"{v.watermark_path} has no subject_sha")
    since = subj.resolve(str(mark["subject_sha"]))
    until = subj.resolve(until)
    report = SweepReport(since=since, until=until)
    if since == until:
        return report
    report.commits = subj.commits_between(since, until)

    old, new = subj.symbols(since), subj.symbols(until)
    owner = v.cfg.owner
    cited: dict[str, list[str]] = {}
    citing_modules: dict[str, set[str]] = {}
    for r in v.active_rules:
        for s in r.code:
            cited.setdefault(s, []).append(r.id)
            citing_modules.setdefault(s, set()).add(r.module)

    for key in sorted(set(old) | set(new)):
        if key in old and key in new:
            if old[key].source == new[key].source:
                continue
            kind, sym = "changed", new[key]
        elif key in new:
            kind, sym = "added", new[key]
        else:
            kind, sym = "removed", old[key]
        if key in v.cfg.ignored and kind == "changed":
            continue
        report.changes.append(
            Change(
                symbol=key,
                kind=kind,
                module=owner.get(key, ""),
                rules=tuple(cited.get(key, [])),
                location=f"{sym.file}:{sym.line}",
                cited_by=tuple(sorted(citing_modules.get(key, set()) - {owner.get(key, "")})),
            )
        )
    return report


def advance(
    v: Vault,
    subj: Subject,
    report: SweepReport,
    reviewed: list[str],
    note: str,
    today: date | None = None,
) -> None:
    """Move the watermark, recording who reviewed what. Refuses a partial review."""
    if not report.behind:
        raise ValueError("already up to date")
    unknown = set(reviewed) - {m.name for m in v.cfg.modules}
    if unknown:
        raise ValueError(f"unknown module(s): {', '.join(sorted(unknown))}")
    missing = set(report.stale_modules) - set(reviewed)
    if missing:
        raise ValueError(
            "these modules changed and were not reviewed: " + ", ".join(sorted(missing))
        )
    if report.unowned:
        raise ValueError(
            "new code belongs to no module: "
            + ", ".join(c.symbol for c in report.unowned)
            + ". Give it a module in vault.yaml first."
        )
    today = today or date.today()
    v.watermark_path.write_text(
        yaml.safe_dump({"subject_sha": report.until, "reviewed_on": today.isoformat()}),
        encoding="utf-8",
    )
    row = (
        f"| {today.isoformat()} | `{report.since[:7]}` | `{report.until[:7]}` | "
        f"{len(report.commits)} | {', '.join(report.stale_modules) or 'none'} | "
        f"{', '.join(sorted(reviewed)) or 'none'} | {note.replace('|', '/')} |\n"
    )
    log = v.run_log_path
    if not log.exists():
        log.write_text(
            "# Release maintenance run log\n\n"
            "| Date | From | To | Commits | Modules changed | Reviewed | Note |\n"
            "|---|---|---|---:|---|---|---|\n",
            encoding="utf-8",
        )
    with log.open("a", encoding="utf-8") as f:
        f.write(row)
