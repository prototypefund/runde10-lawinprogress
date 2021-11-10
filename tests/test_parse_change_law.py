"""Test the functions for change law parsing."""
import pytest

from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import (
    Change,
    parse_change_law_tree,
    parse_change_location,
    parse_change_request_line,
    parse_change_sentences,
    parse_change_text,
)


def test_create_change_object():
    """Test if a change object can be successfully created."""
    change = Change(
        location=["§ 1"], sentences=[], text=["test", "text"], change_type="cancelled"
    )


def test_parse_change_location_success():
    """Test if the location from a single line can be parsed."""
    line = "5. - § 9 wird wie folgt geändert: a) - In Absatz 1 wird das Wort „befahrbaren“ durch die Wörter „zum Befahren  bestimmten“ ersetzt."
    location = parse_change_location(line)

    assert len(location) == 2
    assert location[0] == "§ 9"
    assert location[1] == "Absatz 1"


def test_parse_change_sentences_success():
    """Test if sentences identifiers can be successfully parsed."""
    line = "5. - § 9 wird wie folgt geändert: b) - In Absatz 4 werden die Sätze 5 bis 7 aufgehoben."
    sentences = parse_change_sentences(line)

    assert len(sentences) == 1
    assert sentences[0] == "Sätze 5 bis 7"


def test_parse_change_text_success():
    """Test if change text can be successfully parsed."""
    line = "5. - § 9 wird wie folgt geändert: a) - In Absatz 1 wird das Wort „befahrbaren“ durch die Wörter „zum Befahren  bestimmten“ ersetzt."
    change_text = parse_change_text(line)

    assert len(change_text) == 2
    assert change_text[0] == "befahrbaren"
    assert change_text[1] == "zum Befahren  bestimmten"


def test_parse_change_request_line_renumbering():
    """Test if a renumbering change is correctly parsed."""
    line = (
        "4. - § 7 wird wie folgt geändert: b) - Der bisherige Absatz 7 wird Absatz 8."
    )
    parsed_change = parse_change_request_line(line)

    assert len(parsed_change) == 1
    assert parsed_change[0].change_type == "RENUMBERING"
    assert parsed_change[0].text == []
    assert parsed_change[0].sentences == []
    assert parsed_change[0].location == ["§ 7"]


def test_parse_change_request_line_success():
    """Test if a usual change line is correctly parsed."""
    line = "3. - In § 5 Absatz 1 Satz 2 werden die Wörter „auf Antrag und“ gestrichen."
    parsed_change = parse_change_request_line(line)

    assert len(parsed_change) == 1
    assert parsed_change[0].change_type == "delete_after"
    assert parsed_change[0].text == ["auf Antrag und"]
    assert parsed_change[0].sentences == ["Satz 2"]
    assert parsed_change[0].location == ["§ 5", "Absatz 1"]


def test_parse_change_request_line_muliple():
    """Test if multiple changes in one request lien are correctly escalated."""
    line = "13. - § 28 Absatz 1 wird wie folgt geändert: e) - In Satz 2 werden die Wörter „auf Antrag und“ gestrichen und es werden nach dem Wort „Kennzeichen“die Wörter „, gültige Versicherungskennzeichen oder gültige Versicherungsplaketten“eingefügt."
    parsed_change = parse_change_request_line(line)

    assert len(parsed_change) == 1
    assert parsed_change[0].change_type == "MULTIPLE_CHANGES"


def test_parse_change_law_tree():
    """Test if a simple short law can be parsed successfully."""
    raw_text = "'1. In der Inhaltsübersicht wird nach der Angabe zu § 11 folgende Angabe eingefügt:„§ 11a Sondernutzung für das gewerbliche Anbieten von Mietfahrzeugen“.\n2. In § 2 Absatz 2 Nummer 1 Buchstabe b wird das Wort „Grünanlagen“ durch das Wort„Straßenbegleitgrün“ ersetzt.\n3. In § 5 Absatz 1 Satz 2 werden die Wörter „auf Antrag und“ gestrichen."
    parsed_change_law_tree = LawTextNode(text="Test law tree", bulletpoint="change")
    _ = parse_change_law_tree(raw_text, parsed_change_law_tree)

    expected_tree = """change Test law tree
    2. In § 2 Absatz 2 Nummer 1 Buchstabe b wird das Wort „Grünanlagen“ durch das Wort„Straßenbegleitgrün“ ersetzt.
    3. In § 5 Absatz 1 Satz 2 werden die Wörter „auf Antrag und“ gestrichen.
"""
    assert parsed_change_law_tree.to_text() == expected_tree
