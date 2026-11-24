from __future__ import annotations

from quality_vault import mdtable


def test_pipes_inside_code_or_escaped_stay_in_the_cell():
    assert mdtable.split_cells("| a | `x | y` | b \\| c |") == ["a", "`x | y`", "b | c"]


def test_tables_inside_code_fences_are_ignored(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text(
        "---\nmodule: x\n---\n"
        "```\n| ID | Rule |\n|---|---|\n| no | no |\n```\n\n"
        "| ID | Rule |\n|---|---|\n| A-R01 | yes |\n"
    )
    doc = mdtable.parse(p)
    assert doc.meta == {"module": "x"}
    assert len(doc.tables) == 1
    row = doc.tables[0].rows[0]
    assert row["ID"] == "A-R01"
    assert row.line == 12


def test_short_rows_are_padded():
    p_cells = mdtable.split_cells("| one |")
    assert p_cells == ["one"]


def test_split_list_strips_code_marks():
    assert mdtable.split_list("`a.b`, `c.d`; e") == ["a.b", "c.d", "e"]
