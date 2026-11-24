"""Each test plants one kind of drift and proves `qv check` names it."""

from __future__ import annotations

import pytest

from quality_vault import config


def test_a_vault_that_matches_its_app_passes(world):
    assert world.problems() == []
    assert world.problems("warning") == []
    assert world.qv("check") == 0


def test_a_rule_citing_code_that_does_not_exist_fails(world):
    # The hallucination guard: a spec cannot describe a function the app does not have.
    world.edit(
        "vault/02-Modules/tickets/Behavior-Spec.md", "services.open_ticket", "services.create"
    )
    problems = world.problems()
    assert any(p.code == "Q004" and "services.create" in p.message for p in problems)
    assert world.qv("check") == 1


def test_renaming_a_function_in_the_app_breaks_the_rules_that_cite_it(world):
    world.edit("app-repo/src/app/services.py", "def open_ticket(", "def create_ticket(")
    codes = world.codes()
    assert "Q004" in codes  # TK-R01 cites the old name
    assert "Q010" in codes  # the new name belongs to no module
    assert "Q011" in codes  # vault.yaml still lists the old name


def test_new_code_with_no_module_fails(world):
    world.edit(
        "app-repo/src/app/services.py",
        "def close_ticket(",
        "def reopen_ticket(ticket):\n    return ticket\n\n\ndef close_ticket(",
    )
    problems = [p for p in world.problems() if p.code != "Q060"]  # the code map moved too
    assert [p.code for p in problems] == ["Q010"]
    assert "services.reopen_ticket belongs to no module" in problems[0].message


def test_deleting_a_rule_fails_but_retiring_it_passes(world):
    spec = "vault/02-Modules/tickets/Behavior-Spec.md"
    world.edit(spec, "| TK-R01 | A ticket needs a title. | `services.open_ticket` | v1 |\n", "")
    world.edit("vault/03-Test-Cases/tickets.md", "| TK-TC01 | TK-R01 |", "| TK-TC01 | TK-R02 |")
    assert "Q006" in world.codes()

    world.edit(
        spec,
        "| TK-R02 |",
        "| TK-R01 | Retired 2026-02-01: titles became optional. | | v1 |\n| TK-R02 |",
    )
    world.qv("generate")
    assert world.problems() == []


def test_a_new_rule_id_must_be_locked(world):
    world.edit(
        "vault/02-Modules/tickets/Behavior-Spec.md",
        "| TK-R02 |",
        "| TK-R03 | A done ticket stays done. | `services.close_ticket` | v2 |\n| TK-R02 |",
    )
    world.edit(
        "vault/03-Test-Cases/tickets.md",
        "| TK-TC03 |",
        "| TK-TC04 | TK-R03 | service | Done stays done. | — | |\n| TK-TC03 |",
    )
    assert world.codes() == {"Q007", "Q060"}
    assert world.qv("lock") == 0
    assert world.qv("generate") == 0
    assert world.problems() == []


def test_a_rule_with_no_test_case_fails(world):
    world.edit(
        "vault/02-Modules/tickets/Behavior-Spec.md",
        "| TK-R02 |",
        "| TK-R03 | Titles are trimmed. | `services.open_ticket` | v2 |\n| TK-R02 |",
    )
    world.qv("lock")
    problems = world.problems()
    assert any(p.code == "Q025" and "TK-R03" in p.message for p in problems)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("test_open_needs_a_title`", "test_open_needs_a_titel`"),
        ("TestClose::test_only", "TestClosing::test_only"),
        ("contract:tickets/done", "contract:tickets/closed"),
    ],
)
def test_automation_must_point_at_a_real_test_or_contract_state(world, old, new):
    world.edit("vault/03-Test-Cases/tickets.md", old, new)
    assert "Q024" in world.codes()


def test_high_layers_must_say_why_a_lower_one_cannot_prove_it(world):
    tc = "vault/03-Test-Cases/tickets.md"
    world.edit(tc, "| TK-TC03 | TK-R02 | service |", "| TK-TC03 | TK-R02 | e2e |")
    assert "Q023" in world.codes()
    world.edit(
        tc, "| `contract:tickets/done` | |", "| `contract:tickets/done` | The badge is UI-only. |"
    )
    assert "Q023" not in world.codes()


def test_unknown_layer_fails(world):
    world.edit(
        "vault/03-Test-Cases/tickets.md",
        "| TK-TC01 | TK-R01 | service |",
        "| TK-TC01 | TK-R01 | smoke |",
    )
    assert "Q022" in world.codes()


def test_a_new_enum_value_in_the_code_needs_a_data_decision(world):
    world.edit(
        "app-repo/src/app/models.py", 'DONE = "DONE"', 'DONE = "DONE"\n    BLOCKED = "BLOCKED"'
    )
    problems = world.problems()
    assert any(p.code == "Q032" and "Status.BLOCKED" in p.message for p in problems)

    world.edit(
        "vault/04-Data-Setup/tickets.md",
        "| Title |",
        "| Status | BLOCKED | `gap` | Not seeded yet. |\n| Title |",
    )
    assert "Q032" not in world.codes()


def test_a_removed_enum_value_makes_the_inventory_stale(world):
    world.edit("app-repo/src/app/models.py", '    DONE = "DONE"\n', "")
    assert "Q033" in world.codes()


def test_data_must_cite_a_real_seed_state_or_say_why_not(world):
    data = "vault/04-Data-Setup/tickets.md"
    world.edit(data, "`tickets/open`", "`tickets/opened`")
    assert "Q030" in world.codes()
    world.edit(data, "`tickets/opened`", "`tickets/open`")
    world.edit(data, "Nobody seeded a 500-character title yet.", "")
    assert "Q031" in world.codes()


def test_findings_register_refuses_a_duplicate_signature(world):
    world.edit(
        "vault/06-Findings/Register.md",
        "\n\nText below",
        "\n| TF-002 | 2026-01-03 | tickets | Double close crashes. | `tickets:close:double-close-crash` "
        "| R3 | open | `pytest -q` |\n\nText below",
    )
    problems = world.problems()
    assert any(p.code == "Q041" and "TF-001" in p.message for p in problems)


@pytest.mark.parametrize(
    ("column_old", "column_new", "code"),
    [
        ("| R3 | fixed", "| R9 | fixed", "Q043"),
        ("| R3 | fixed 2026-01-02 |", "| R3 | sort of |", "Q043"),
        ("| fixed 2026-01-02 | `pytest -q -k close` |", "| open | |", "Q044"),
        ("| TF-001 |", "| F-1 |", "Q040"),
    ],
)
def test_findings_rows_are_complete(world, column_old, column_new, code):
    world.edit("vault/06-Findings/Register.md", column_old, column_new)
    assert code in world.codes()


def test_the_mind_map_must_name_every_module(world):
    world.edit("vault/01-System-Map/Mind-Map.md", "    tickets\n", "    other\n")
    assert "Q050" in world.codes()


def test_generated_pages_fail_when_stale_and_keep_hand_written_text(world):
    dash = world.vault_dir / "00-Home/Dashboard.md"
    dash.write_text(dash.read_text().replace("# Dashboard", "# Dashboard\n\nOur notes."))
    assert world.problems() == []  # text outside the markers is not generated

    world.edit(
        "vault/03-Test-Cases/tickets.md", "`tests/test_app.py::test_open_needs_a_title`", "—"
    )
    assert world.codes() == {"Q060"}
    assert world.qv("generate") == 0
    assert world.problems() == []
    text = dash.read_text()
    assert "Our notes." in text
    assert "TK-R01" in text  # now listed under "Rules with no automated test yet"


def test_missing_vault_file_is_reported(world):
    (world.vault_dir / "04-Data-Setup/tickets.md").unlink()
    assert "Q001" in world.codes()


def test_a_bare_yaml_boolean_prefix_is_refused(world):
    # YAML 1.1 reads OFF, NO and ON as booleans. That once crashed this tool.
    world.edit("vault.yaml", 'prefix: "TK"', "prefix: OFF")
    with pytest.raises(config.ConfigError, match="quoted string"):
        world.load()


def test_a_symbol_owned_twice_is_refused(world):
    yml = world.root / "vault.yaml"
    yml.write_text(
        yml.read_text() + '  more:\n    prefix: "MO"\n    symbols: [services.open_ticket]\n'
    )
    with pytest.raises(config.ConfigError, match="owned by both"):
        world.load()
