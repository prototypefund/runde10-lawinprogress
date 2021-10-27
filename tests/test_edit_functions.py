"""Test the edit functions to apply changes."""
from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import Change

from lawinprogress.apply_changes.edit_functions import _replace, _insert_after


def test_replace_success():
    """Test if text in a node can be replaced properly."""
    node = LawTextNode(bulletpoint="(1)", text="Test text to replace;")
    change = Change(location="(1)", sentences=[], text=["text to replace", "replaced"], change_type="replace")

    status = _replace(node, change)

    assert status == 1
    assert node.text == "Test replaced;"


def test_replace_failure():
    """Test if replace fails as expected."""
    node = LawTextNode(bulletpoint="(1)", text="Test text to replace;")
    change = Change(location="(1)", sentences=[], text=["text to replace"], change_type="replace")

    status = _replace(node, change)

    assert status == 0
    assert node.text == "Test text to replace;"


def test_insert_after_with_paired_texts():
    """Test if insert_after works fine if the text comes in pairs (location, text_to_insert)."""

    node = LawTextNode(bulletpoint="(1)", text="Test text insert here;")
    change = Change(location="(1)", sentences=[], text=["insert", "inserted"], change_type="insert_after")

    status = _insert_after(node, change)

    assert status == 1
    assert node.text == "Test text insert inserted here;"


def test_insert_after_fails_with_no_text():
    """Test if insert_after fails if no text is given."""
    node = LawTextNode(bulletpoint="(1)", text="Test text to replace;")
    change = Change(location="(1)", sentences=[], text=[], change_type="insert_after")

    status = _insert_after(node, change)

    assert status == 0
