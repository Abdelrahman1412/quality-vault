"""`qv check`: every way the vault can drift from the code, as a failing check.

A vault that nobody checks rots silently, and an agent that trusts a rotten
vault is worse off than one that reads the code. So the vault only claims
what these checks can hold it to.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from quality_vault import generate
from quality_vault.subject import Subject
from quality_vault.vault import (
    TEST_CASES,
    Vault,
    rule_id_pattern,
    tc_id_pattern,
)

RANKS = {"R1", "R2", "R3", "R4"}
STATUSES = {"open", "fixed", "stale", "wontfix", "limit"}
FINDING_ID = re.compile(r"^TF-\d{3,}$")
SEED_KEYWORDS = {"gap", "limit"}


@dataclass(frozen=True)
class Problem:
    code: str
    where: str
    message: str
    severity: str = "error"  # error fails the check; warning is reported only

    def render(self) -> str:
        return f"{self.severity.upper():7} {self.code} {self.where}: {self.message}"


def check_specs(v: Vault, subj: Subject) -> list[Problem]:
    out: list[Problem] = []
    code = subj.current
    for path in v.missing:
        out.append(Problem("Q001", path, "missing vault file or table"))

    counts = Counter(r.id for r in v.rules)
    for r in v.rules:
        prefix = v.cfg.module(r.module).prefix
        if not rule_id_pattern(prefix).match(r.id):
            out.append(
                Problem("Q002", r.row.where, f"rule id '{r.id}' must look like {prefix}-R01")
            )
        if counts[r.id] > 1:
            out.append(Problem("Q003", r.row.where, f"rule id {r.id} is used more than once"))
        if r.retired:
            continue
        if not r.code:
            out.append(Problem("Q004", r.row.where, f"{r.id} cites no code; name the symbol"))
        for sym in r.code:
            if sym not in code:
                out.append(
                    Problem("Q004", r.row.where, f"{r.id} cites {sym}, which is not in the code")
                )

    ids = {r.id for r in v.rules}
    for locked in v.locked_ids:
        if locked not in ids:
            out.append(
                Problem(
                    "Q006",
                    str(v.lock_path),
                    f"{locked} was issued but is gone. Rule ids are never deleted or "
                    "renumbered: keep the row and start its text with 'Retired'",
                )
            )
    for rid in sorted(ids - set(v.locked_ids)):
        out.append(Problem("Q007", str(v.lock_path), f"{rid} is not in the lock; run `qv lock`"))
    return out


def check_code_ownership(v: Vault, subj: Subject) -> list[Problem]:
    """New code must land in a module, so it cannot ship without a spec."""
    out: list[Problem] = []
    owner = v.cfg.owner
    code = subj.current
    for key, sym in sorted(code.items()):
        if key not in owner and key not in v.cfg.ignored:
            out.append(
                Problem(
                    "Q010",
                    f"{sym.file}:{sym.line}",
                    f"{key} belongs to no module; add it to a module in vault.yaml "
                    "(and to that module's spec) or to `ignore` with a reason",
                )
            )
    for key in sorted(set(owner) | set(v.cfg.ignored)):
        if key not in code:
            out.append(Problem("Q011", "vault.yaml", f"{key} is configured but not in the code"))

    cited = {(r.module, s) for r in v.active_rules for s in r.code}
    for m in v.cfg.modules:
        for s in m.symbols:
            if s in code and (m.name, s) not in cited:
                out.append(
                    Problem(
                        "Q012",
                        str(v.spec_path(m)),
                        f"no {m.name} rule cites {s}",
                        severity="warning",
                    )
                )
    return out


def check_test_cases(v: Vault, subj: Subject) -> list[Problem]:
    out: list[Problem] = []
    rules = {r.id: r for r in v.rules}
    layers = v.cfg.layers
    justify_at = layers.index(v.cfg.justify_from) if v.cfg.justify_from else len(layers)
    counts = Counter(tc.id for tc in v.test_cases)
    for tc in v.test_cases:
        prefix = v.cfg.module(tc.module).prefix
        if not tc_id_pattern(prefix).match(tc.id):
            out.append(
                Problem("Q020", tc.row.where, f"test case id '{tc.id}' must be {prefix}-TC01")
            )
        if counts[tc.id] > 1:
            out.append(
                Problem("Q026", tc.row.where, f"test case id {tc.id} is used more than once")
            )
        if not tc.rules:
            out.append(Problem("Q021", tc.row.where, f"{tc.id} proves no rule"))
        for rid in tc.rules:
            if rid not in rules:
                out.append(Problem("Q021", tc.row.where, f"{tc.id} cites unknown rule {rid}"))
            elif rules[rid].retired:
                out.append(Problem("Q021", tc.row.where, f"{tc.id} cites retired rule {rid}"))
        if tc.layer not in layers:
            out.append(
                Problem("Q022", tc.row.where, f"{tc.id} layer '{tc.layer}' is not one of {layers}")
            )
        elif layers.index(tc.layer) >= justify_at and not tc.why_layer.strip():
            out.append(
                Problem(
                    "Q023",
                    tc.row.where,
                    f"{tc.id} sits at '{tc.layer}'; say in 'Why this layer' why a lower layer "
                    "cannot prove it",
                )
            )
        for ref in tc.automated_by:
            if ref.startswith("contract:"):
                state = ref.removeprefix("contract:")
                if state not in subj.seed_states:
                    out.append(
                        Problem("Q024", tc.row.where, f"{tc.id}: no seed contract state '{state}'")
                    )
            elif not subj.test_exists(ref):
                out.append(Problem("Q024", tc.row.where, f"{tc.id}: test {ref} does not exist"))

    proved = {rid for tc in v.test_cases for rid in tc.rules}
    for r in v.active_rules:
        if r.id not in proved:
            out.append(
                Problem(
                    "Q025",
                    r.row.where,
                    f"{r.id} has no test case in {TEST_CASES}/{r.module}.md",
                )
            )
    return out


def check_data(v: Vault, subj: Subject) -> list[Problem]:
    out: list[Problem] = []
    for d in v.data:
        if d.seed_state in SEED_KEYWORDS:
            if not d.notes.strip():
                out.append(
                    Problem(
                        "Q031",
                        d.row.where,
                        f"{d.variable}={d.value} is a {d.seed_state}; say why in Notes",
                    )
                )
        elif d.seed_state not in subj.seed_states:
            out.append(
                Problem(
                    "Q030",
                    d.row.where,
                    f"{d.variable}={d.value}: seed state '{d.seed_state}' is not in the seed "
                    "contract (use a contract id, enum/<column>, gap or limit)",
                )
            )

    listed: dict[str, set[str]] = defaultdict(set)
    for d in v.data:
        listed[d.variable].add(d.value)
    for enum, members in sorted(subj.enums.items()):
        for member in members:
            if member not in listed.get(enum, set()):
                out.append(
                    Problem(
                        "Q032",
                        "04-Data-Setup",
                        f"{enum}.{member} is in the code but in no data inventory",
                    )
                )
    for d in v.data:
        members = subj.enums.get(d.variable)
        if members is not None and d.value not in members:
            out.append(
                Problem("Q033", d.row.where, f"{d.variable} has no member {d.value} any more")
            )
    return out


def check_findings(v: Vault) -> list[Problem]:
    out: list[Problem] = []
    ids = Counter(f.id for f in v.findings)
    sigs: dict[str, str] = {}
    for f in v.findings:
        where = f.row.where
        if not FINDING_ID.match(f.id):
            out.append(Problem("Q040", where, f"finding id '{f.id}' must look like TF-001"))
        if ids[f.id] > 1:
            out.append(Problem("Q040", where, f"finding id {f.id} is used more than once"))
        for column in ("Found", "Area", "Finding", "Signature"):
            if not f.row[column].strip():
                out.append(Problem("Q042", where, f"{f.id}: '{column}' is empty"))
        if f.signature:
            if f.signature in sigs:
                out.append(
                    Problem(
                        "Q041",
                        where,
                        f"{f.id} duplicates {sigs[f.signature]} (same signature "
                        f"'{f.signature}'); update that row instead",
                    )
                )
            sigs.setdefault(f.signature, f.id)
        if f.rank not in RANKS:
            out.append(Problem("Q043", where, f"{f.id}: rank '{f.rank}' is not one of R1-R4"))
        if f.status.split()[0:1] and f.status.split()[0] not in STATUSES:
            out.append(Problem("Q043", where, f"{f.id}: status '{f.status}' is not recognised"))
        if f.status.startswith("open") and not f.reverify:
            out.append(Problem("Q044", where, f"{f.id} is open with no re-verify command"))
    return out


def check_system_map(v: Vault) -> list[Problem]:
    path = v.dir / "01-System-Map" / "Mind-Map.md"
    if not path.exists():
        return [Problem("Q050", str(path), "the mind map is missing")]
    text = path.read_text(encoding="utf-8").lower()
    return [
        Problem("Q050", str(path), f"module '{m.name}' is not on the mind map")
        for m in v.cfg.modules
        if m.name.lower() not in text
    ]


def check_generated(v: Vault, subj: Subject) -> list[Problem]:
    out: list[Problem] = []
    for path, expected in generate.render_all(v, subj).items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != expected:
            out.append(Problem("Q060", str(path), "out of date; run `qv generate`"))
    return out


def run(v: Vault, subj: Subject) -> list[Problem]:
    return [
        *check_specs(v, subj),
        *check_code_ownership(v, subj),
        *check_test_cases(v, subj),
        *check_data(v, subj),
        *check_findings(v),
        *check_system_map(v),
        *check_generated(v, subj),
    ]
