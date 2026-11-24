"""The vault's content, loaded from Markdown into plain objects."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from quality_vault import mdtable
from quality_vault.config import Config, Module
from quality_vault.mdtable import Row

SPECS = "02-Modules"
TEST_CASES = "03-Test-Cases"
DATA = "04-Data-Setup"
RELEASE = "05-Release-Maintenance"
FINDINGS = "06-Findings"

RULE_COLUMNS = ("ID", "Rule", "Code")
TC_COLUMNS = ("ID", "Rules", "Layer", "Case", "Automated by")
DATA_COLUMNS = ("Variable", "Value", "Seed state", "Notes")
FINDING_COLUMNS = (
    "ID",
    "Found",
    "Area",
    "Finding",
    "Signature",
    "Rank",
    "Status",
    "Re-verify",
)
NOT_AUTOMATED = {"", "-", "—", "none"}


@dataclass
class Rule:
    id: str
    text: str
    code: list[str]
    module: str
    row: Row

    @property
    def retired(self) -> bool:
        return self.text.lower().startswith("retired")


@dataclass
class TestCase:
    id: str
    rules: list[str]
    layer: str
    case: str
    automated_by: list[str]
    why_layer: str
    module: str
    row: Row

    @property
    def automated(self) -> bool:
        return bool(self.automated_by)


@dataclass
class DataValue:
    variable: str
    value: str
    seed_state: str
    notes: str
    module: str
    row: Row


@dataclass
class Finding:
    row: Row

    def _cell(self, column: str) -> str:
        return mdtable.strip_code(self.row[column])

    @property
    def id(self) -> str:
        return self._cell("ID")

    @property
    def area(self) -> str:
        return self._cell("Area")

    @property
    def signature(self) -> str:
        return self._cell("Signature")

    @property
    def rank(self) -> str:
        return self._cell("Rank")

    @property
    def status(self) -> str:
        return self._cell("Status").lower()

    @property
    def title(self) -> str:
        return self.row["Finding"]

    @property
    def reverify(self) -> str:
        return mdtable.strip_code(self.row["Re-verify"])


@dataclass
class Vault:
    cfg: Config
    rules: list[Rule] = field(default_factory=list)
    test_cases: list[TestCase] = field(default_factory=list)
    data: list[DataValue] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # files a module should have but lacks
    locked_ids: list[str] = field(default_factory=list)

    @property
    def dir(self) -> Path:
        return self.cfg.vault_dir

    def spec_path(self, m: Module) -> Path:
        return self.dir / SPECS / m.name / "Behavior-Spec.md"

    def tc_path(self, m: Module) -> Path:
        return self.dir / TEST_CASES / f"{m.name}.md"

    def data_path(self, m: Module) -> Path:
        return self.dir / DATA / f"{m.name}.md"

    @property
    def lock_path(self) -> Path:
        return self.dir / SPECS / "rule-ids.lock"

    @property
    def register_path(self) -> Path:
        return self.dir / FINDINGS / "Register.md"

    @property
    def watermark_path(self) -> Path:
        return self.dir / RELEASE / "watermark.yaml"

    @property
    def run_log_path(self) -> Path:
        return self.dir / RELEASE / "Run-Log.md"

    def watermark(self) -> dict:
        if not self.watermark_path.exists():
            return {}
        return yaml.safe_load(self.watermark_path.read_text(encoding="utf-8")) or {}

    @property
    def active_rules(self) -> list[Rule]:
        return [r for r in self.rules if not r.retired]


def _table(path: Path, columns: tuple[str, ...], missing: list[str]) -> list[Row]:
    if not path.exists():
        missing.append(str(path))
        return []
    doc = mdtable.parse(path)
    table = doc.table_with(*columns)
    if table is None:
        missing.append(f"{path} (no table with columns {', '.join(columns)})")
        return []
    return table.rows


def load(cfg: Config) -> Vault:
    v = Vault(cfg=cfg)
    for m in cfg.modules:
        for row in _table(v.spec_path(m), RULE_COLUMNS, v.missing):
            v.rules.append(
                Rule(
                    id=mdtable.strip_code(row["ID"]),
                    text=row["Rule"],
                    code=mdtable.split_list(row["Code"]),
                    module=m.name,
                    row=row,
                )
            )
        for row in _table(v.tc_path(m), TC_COLUMNS, v.missing):
            auto = mdtable.split_list(row["Automated by"])
            v.test_cases.append(
                TestCase(
                    id=mdtable.strip_code(row["ID"]),
                    rules=mdtable.split_list(row["Rules"]),
                    layer=mdtable.strip_code(row["Layer"]).lower(),
                    case=row["Case"],
                    automated_by=[a for a in auto if a.lower() not in NOT_AUTOMATED],
                    why_layer=row["Why this layer"],
                    module=m.name,
                    row=row,
                )
            )
        for row in _table(v.data_path(m), DATA_COLUMNS, v.missing):
            v.data.append(
                DataValue(
                    variable=mdtable.strip_code(row["Variable"]),
                    value=mdtable.strip_code(row["Value"]),
                    seed_state=mdtable.strip_code(row["Seed state"]),
                    notes=row["Notes"],
                    module=m.name,
                    row=row,
                )
            )
    if v.register_path.exists():
        v.findings = [Finding(r) for r in _table(v.register_path, FINDING_COLUMNS, v.missing)]
    if v.lock_path.exists():
        v.locked_ids = [
            line.strip()
            for line in v.lock_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
    return v


def rule_id_pattern(prefix: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(prefix)}-R\d{{2,}}$")


def tc_id_pattern(prefix: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(prefix)}-TC\d{{2,}}$")
