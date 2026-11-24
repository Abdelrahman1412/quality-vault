"""The findings register: one row per finding, and every open one re-checkable."""

from __future__ import annotations

from datetime import date

import pytest

from quality_vault import findings


def add(world, **kw):
    v, _ = world.load()
    args = {
        "area": "tickets",
        "title": "Titles longer than 200 characters are cut without warning.",
        "signature": "tickets:open:title-truncated",
        "rank": "R3",
        "reverify": "pytest -q -k long_title",
        "today": date(2026, 2, 1),
    } | kw
    return findings.add(v, **args)


def test_add_appends_the_next_id_inside_the_table(world):
    assert add(world) == "TF-002"
    v, _ = world.load()
    assert [f.id for f in v.findings] == ["TF-001", "TF-002"]
    assert v.findings[1].status == "open"
    assert v.register_path.read_text().rstrip().endswith("Text below the table stays put.")
    assert world.problems() == [] or {p.code for p in world.problems()} == {"Q060"}


def test_same_signature_is_refused_whatever_the_wording(world):
    with pytest.raises(ValueError, match="TF-001"):
        add(world, title="Something else entirely", signature="Tickets:Close:Double close crash")


def test_a_near_identical_title_is_refused(world):
    with pytest.raises(ValueError, match=r"TF-001.*similar"):
        add(
            world,
            title="Closing a closed ticket crashed, instead of refusing it",
            signature="x:y:z",
        )


def test_an_unrelated_finding_is_accepted(world):
    assert add(world) == "TF-002"


def test_a_finding_needs_a_reverify_command(world):
    with pytest.raises(ValueError, match="re-verify"):
        add(world, reverify="  ")


def test_cli_add_reports_the_duplicate_and_exits_1(world, capsys):
    code = world.qv(
        "finding", "add", "--area", "tickets", "--title", "Double close crashes",
        "--signature", "tickets:close:double-close-crash", "--rank", "R3", "--reverify", "true",
    )  # fmt: skip
    assert code == 1
    assert "TF-001" in capsys.readouterr().err


def test_reverify_runs_open_findings_in_the_app_checkout(world):
    add(world, reverify="test -f src/app/services.py && exit 1")
    add(
        world,
        title="Nothing checks the done count.",
        signature="tickets:count:unchecked",
        reverify="test -f does-not-exist.txt",
    )
    v, s = world.load()
    results = {r.finding.id: r for r in findings.reverify_open(v, s)}
    assert set(results) == {"TF-002", "TF-003"}  # TF-001 is fixed, so it is not re-run
    assert results["TF-002"].verdict == "still reproduces"
    assert results["TF-003"].verdict == "still reproduces"

    (s.root / "does-not-exist.txt").write_text("now it does")
    results = {r.finding.id: r for r in findings.reverify_open(v, s)}
    assert results["TF-003"].verdict.startswith("clean")


def test_similarity_ignores_filler_words():
    assert findings.similarity("The ticket is closed", "ticket closed") == 1.0
    assert findings.similarity("payslip rounding", "leave overlap") == 0.0
