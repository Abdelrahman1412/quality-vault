"""Release maintenance: the sweep finds what changed; the watermark moves only after a full review."""

from __future__ import annotations

from datetime import date

import pytest
import yaml

from quality_vault import sweep


def test_up_to_date_vault_reports_nothing(world):
    v, s = world.load()
    report = sweep.sweep(v, s)
    assert not report.behind
    assert world.qv("sweep") == 0


def test_a_changed_function_names_its_module_and_the_rules_to_reread(world):
    world.edit("app-repo/src/app/services.py", "a ticket needs a title", "title required")
    world.commit_app("reword the error")
    v, s = world.load()
    report = sweep.sweep(v, s)

    assert report.behind
    assert [(c.symbol, c.kind, c.module, c.rules) for c in report.changes] == [
        ("services.open_ticket", "changed", "tickets", ("TK-R01",))
    ]
    assert report.stale_modules == ["tickets"]
    assert "rules to re-read: TK-R01" in report.render()
    assert world.qv("sweep") == 1


def test_a_change_outside_any_symbol_is_not_flagged(world):
    world.edit(
        "app-repo/src/app/services.py",
        "from app.models import Status",
        "from app.models import Status  # noqa",
    )
    world.commit_app("comment on an import")
    v, s = world.load()
    report = sweep.sweep(v, s)
    assert report.behind and report.changes == []


def test_new_code_blocks_the_watermark_until_it_has_a_module(world):
    world.edit(
        "app-repo/src/app/services.py",
        "def close_ticket(",
        "def reopen_ticket(ticket):\n    return ticket\n\n\ndef close_ticket(",
    )
    world.commit_app("reopen")
    v, s = world.load()
    report = sweep.sweep(v, s)
    assert [c.symbol for c in report.unowned] == ["services.reopen_ticket"]
    with pytest.raises(ValueError, match="belongs to no module"):
        sweep.advance(v, s, report, ["tickets"], "note")


def test_a_partial_review_does_not_move_the_watermark(world):
    world.edit("app-repo/src/app/services.py", "only open tickets close", "already closed")
    world.commit_app("reword")
    v, s = world.load()
    before = v.watermark_path.read_text()
    report = sweep.sweep(v, s)
    with pytest.raises(ValueError, match="not reviewed: tickets"):
        sweep.advance(v, s, report, [], "skipped it")
    assert v.watermark_path.read_text() == before


def test_a_full_review_moves_the_watermark_and_logs_the_run(world):
    world.edit("app-repo/src/app/services.py", "only open tickets close", "already closed")
    new = world.commit_app("reword")
    v, s = world.load()
    report = sweep.sweep(v, s)
    sweep.advance(v, s, report, ["tickets"], "reworded; rules unchanged", today=date(2026, 3, 1))

    assert yaml.safe_load(v.watermark_path.read_text())["subject_sha"] == new
    log = v.run_log_path.read_text()
    assert "| 2026-03-01 |" in log and "reworded; rules unchanged" in log
    assert not sweep.sweep(v, s).behind


def test_removing_a_function_is_reported(world):
    world.edit(
        "app-repo/src/app/services.py",
        SERVICES_CLOSE,
        "",
    )
    world.commit_app("drop close")
    v, s = world.load()
    report = sweep.sweep(v, s)
    assert [(c.symbol, c.kind) for c in report.changes] == [("services.close_ticket", "removed")]


SERVICES_CLOSE = """

def close_ticket(ticket):
    if ticket["status"] != Status.OPEN:
        raise ValueError("only open tickets close")
    ticket["status"] = Status.DONE
    return ticket
"""
