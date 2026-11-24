"""A tiny app in a git repo and a tiny vault that describes it, built fresh for each test."""

from __future__ import annotations

import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

import pytest

from quality_vault import checks, config, generate
from quality_vault import vault as vault_mod
from quality_vault.cli import main
from quality_vault.subject import Subject

MODELS = """\
import enum


class Status(enum.StrEnum):
    OPEN = "OPEN"
    DONE = "DONE"
"""

SERVICES = """\
from app.models import Status


def open_ticket(title):
    if not title:
        raise ValueError("a ticket needs a title")
    return {"title": title, "status": Status.OPEN}


def close_ticket(ticket):
    if ticket["status"] != Status.OPEN:
        raise ValueError("only open tickets close")
    ticket["status"] = Status.DONE
    return ticket
"""

TESTS = """\
def test_open_needs_a_title():
    pass


class TestClose:
    def test_only_open_tickets_close(self):
        pass
"""

CONTRACT = """\
contract:
  states:
    - id: tickets/open
      check: tickets_in_status
    - id: tickets/done
      check: tickets_in_status
  enum_coverage:
    - column: tickets.status
"""

VAULT_YAML = """\
project: Demo
vault_dir: vault
subject:
  path: app-repo
  scan: [src/app/*.py]
  tests: tests
  seed_contract: seed.yaml
test_layers:
  order: [unit, service, api, e2e]
  justify_from: api
modules:
  tickets:
    prefix: "TK"
    symbols: [models.Status, services.open_ticket, services.close_ticket]
"""

SPEC = """\
# Tickets

| ID | Rule | Code | Since |
|---|---|---|---|
| TK-R01 | A ticket needs a title. | `services.open_ticket` | v1 |
| TK-R02 | Only an open ticket can be closed. | `services.close_ticket`, `models.Status` | v1 |
"""

TEST_CASES = """\
# Tickets: test cases

| ID | Rules | Layer | Case | Automated by | Why this layer |
|---|---|---|---|---|---|
| TK-TC01 | TK-R01 | service | Empty title is refused. | `tests/test_app.py::test_open_needs_a_title` | |
| TK-TC02 | TK-R02 | service | Closing a done ticket is refused. | `tests/test_app.py::TestClose::test_only_open_tickets_close` | |
| TK-TC03 | TK-R02 | service | Seed holds a done ticket. | `contract:tickets/done` | |
"""

DATA = """\
# Tickets: data

| Variable | Value | Seed state | Notes |
|---|---|---|---|
| Status | OPEN | `tickets/open` | Ticket 1. |
| Status | DONE | `enum/tickets.status` | Ticket 2. |
| Title | very long | `gap` | Nobody seeded a 500-character title yet. |
"""

REGISTER = """\
# Findings

| ID | Found | Area | Finding | Signature | Rank | Status | Re-verify |
|---|---|---|---|---|---|---|---|
| TF-001 | 2026-01-01 | tickets | Closing a closed ticket crashed instead of refusing. | `tickets:close:double-close-crash` | R3 | fixed 2026-01-02 | `pytest -q -k close` |

Text below the table stays put.
"""

MIND_MAP = "# Mind map\n\n```mermaid\nmindmap\n  root((Demo))\n    tickets\n```\n"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


@dataclass
class World:
    root: Path

    @property
    def app(self) -> Path:
        return self.root / "app-repo"

    @property
    def vault_dir(self) -> Path:
        return self.root / "vault"

    def load(self) -> tuple[vault_mod.Vault, Subject]:
        cfg = config.load(self.root / "vault.yaml")
        return vault_mod.load(cfg), Subject(cfg)

    def problems(self, severity: str = "error") -> list[checks.Problem]:
        v, s = self.load()
        return [p for p in checks.run(v, s) if p.severity == severity]

    def codes(self) -> set[str]:
        return {p.code for p in self.problems()}

    def qv(self, *args: str) -> int:
        return main(["--config", str(self.root / "vault.yaml"), *args])

    def commit_app(self, message: str) -> str:
        git(self.app, "add", "-A")
        git(self.app, "commit", "-q", "-m", message)
        return git(self.app, "rev-parse", "HEAD")

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.root / rel
        text = path.read_text(encoding="utf-8")
        assert old in text, f"{old!r} not in {rel}"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


@pytest.fixture
def world(tmp_path: Path) -> World:
    w = World(tmp_path)
    app = w.app
    write(app / "src/app/models.py", MODELS)
    write(app / "src/app/services.py", SERVICES)
    write(app / "tests/test_app.py", TESTS)
    write(app / "seed.yaml", CONTRACT)
    git(app, "init", "-q", "-b", "main")
    git(app, "config", "user.email", "test@example.com")
    git(app, "config", "user.name", "Test")
    sha = w.commit_app("first release")

    write(tmp_path / "vault.yaml", VAULT_YAML)
    v = w.vault_dir
    write(v / "02-Modules/tickets/Behavior-Spec.md", SPEC)
    write(v / "03-Test-Cases/tickets.md", TEST_CASES)
    write(v / "04-Data-Setup/tickets.md", DATA)
    write(v / "06-Findings/Register.md", REGISTER)
    write(v / "01-System-Map/Mind-Map.md", MIND_MAP)
    write(v / "05-Release-Maintenance/watermark.yaml", f"subject_sha: {sha}\n")
    assert w.qv("lock") == 0
    vault, subj = w.load()
    generate.write_all(vault, subj)
    return w
