"""The app the vault describes. Everything here is read from its code, never assumed."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import yaml

from quality_vault.config import Config

ENUM_BASES = {"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag"}


@dataclass(frozen=True)
class Symbol:
    key: str  # "<file stem>.<name>"
    file: str  # relative to the subject root
    line: int
    source: str
    enum_members: tuple[str, ...] | None = None


def _is_enum(node: ast.ClassDef) -> bool:
    for base in node.bases:
        name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", "")
        if name in ENUM_BASES:
            return True
    return False


def symbols_in(source: str, file: str) -> dict[str, Symbol]:
    """Top-level functions and classes of one Python file, with their exact source."""
    tree = ast.parse(source)
    stem = Path(file).stem
    out: dict[str, Symbol] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        members = None
        if isinstance(node, ast.ClassDef) and _is_enum(node):
            members = tuple(
                t.id
                for stmt in node.body
                if isinstance(stmt, ast.Assign)
                for t in stmt.targets
                if isinstance(t, ast.Name)
            )
        key = f"{stem}.{node.name}"
        out[key] = Symbol(
            key=key,
            file=file,
            line=node.lineno,
            source=ast.get_source_segment(source, node) or "",
            enum_members=members,
        )
    return out


class Subject:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.root = cfg.subject_path
        if not self.root.is_dir():
            raise FileNotFoundError(
                f"subject app not found at {self.root}; set subject.path in vault.yaml "
                "or the QV_SUBJECT environment variable"
            )

    # --- git -------------------------------------------------------------------

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()

    def resolve(self, rev: str) -> str:
        return self.git("rev-parse", f"{rev}^{{commit}}").strip()

    def commits_between(self, old: str, new: str) -> list[str]:
        out = self.git("log", "--format=%h %ad %s", "--date=short", f"{old}..{new}")
        return [line for line in out.splitlines() if line]

    # --- code ------------------------------------------------------------------

    def scanned_files(self, rev: str | None = None) -> list[str]:
        if rev is None:
            files = {
                str(p.relative_to(self.root))
                for pattern in self.cfg.subject_scan
                for p in self.root.glob(pattern)
                if p.is_file()
            }
            return sorted(files)
        listed = self.git("ls-tree", "-r", "--name-only", rev).splitlines()
        return sorted(
            f for f in listed if any(Path(f).match(pattern) for pattern in self.cfg.subject_scan)
        )

    def read(self, file: str, rev: str | None = None) -> str:
        if rev is None:
            return (self.root / file).read_text(encoding="utf-8")
        return self.git("show", f"{rev}:{file}")

    def symbols(self, rev: str | None = None) -> dict[str, Symbol]:
        out: dict[str, Symbol] = {}
        for f in self.scanned_files(rev):
            out.update(symbols_in(self.read(f, rev), f))
        return out

    @cached_property
    def current(self) -> dict[str, Symbol]:
        return self.symbols()

    @cached_property
    def enums(self) -> dict[str, tuple[str, ...]]:
        """Enum class name -> members, e.g. LeaveStatus -> (PENDING, APPROVED, ...)."""
        return {
            s.key.split(".", 1)[1]: s.enum_members
            for s in self.current.values()
            if s.enum_members is not None
        }

    # --- tests -----------------------------------------------------------------

    def test_exists(self, ref: str) -> bool:
        """tests/test_x.py::test_name or tests/test_x.py::Class::method."""
        file, _, path = ref.partition("::")
        target = self.root / file
        if not path or not target.is_file():
            return False
        tree = ast.parse(target.read_text(encoding="utf-8"))
        scope: list[ast.stmt] = tree.body
        for part in path.split("::"):
            found = next(
                (
                    n
                    for n in scope
                    if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
                    and n.name == part
                ),
                None,
            )
            if found is None:
                return False
            scope = found.body if isinstance(found, ast.ClassDef) else []
        return True

    # --- seed contract -----------------------------------------------------------

    @cached_property
    def seed_states(self) -> set[str]:
        """Every state the subject's seed promises, plus enum/<column> coverage entries."""
        if not self.cfg.seed_contract:
            return set()
        raw = yaml.safe_load((self.root / self.cfg.seed_contract).read_text(encoding="utf-8"))
        contract = (raw or {}).get("contract", {})
        states = {s["id"] for s in contract.get("states", [])}
        states |= {f"enum/{e['column']}" for e in contract.get("enum_coverage", [])}
        return states
