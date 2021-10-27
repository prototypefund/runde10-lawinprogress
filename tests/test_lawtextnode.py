"""Test the LawTextNode class and helper functions."""
import pytest

from lawinprogress.parsing.lawtree import LawTextNode


def test_create_tree():
    """Test of a tree can be created."""
    tree = LawTextNode(
        text="Test1",
        bulletpoint="(1)",
    )

    node1 = LawTextNode(
        text="Test2",
        bulletpoint="(2)",
        parent=tree,
    )

    node2 = LawTextNode(
        text="Test3",
        bulletpoint="(3)",
        parent=tree,
    )

    node3 = LawTextNode(
        text="Test4",
        bulletpoint="(4)",
        parent=node1,
    )
    assert tree


def test_print_tree(simple_lawtext_tree):
    """Test the print method of the tree."""
    simple_lawtext_tree._print()


def test_tree_to_text(simple_lawtext_tree):
    """Test the to_text method of the tree."""
    text_tree = """(1) Test1
    (2) Test2
        (4) Test4
    (3) Test3
"""

    tree_text_repr = simple_lawtext_tree.to_text()

    assert text_tree == tree_text_repr


def test_insert_child_new_success(simple_lawtext_tree):
    """Test if a new child can be inserted properly."""
    text_tree = """(1) Test1
    (2) Test2
        (4) Test4
    (3) Test3
    (4) New node
"""

    simple_lawtext_tree.insert_child(text="New node", bulletpoint="(4)")
    tree_text_repr = simple_lawtext_tree.to_text()

    assert text_tree == tree_text_repr


def test_insert_child_already_exists_success(simple_lawtext_tree):
    """Test if a new child can be inserted properly at a place of an already existing node."""
    text_tree = """(1) Test1
    (2) New node
    (3) Test2
        (4) Test4
    (4) Test3
"""

    simple_lawtext_tree.insert_child(text="New node", bulletpoint="(2)")
    tree_text_repr = simple_lawtext_tree.to_text()

    assert text_tree == tree_text_repr


def test_remove_child_success(simple_lawtext_tree):
    """Test if a child node can be removed properly."""
    text_tree = """(1) Test1
    (2) Test3
"""

    simple_lawtext_tree.remove_child(bulletpoint="(2)")
    tree_text_repr = simple_lawtext_tree.to_text()

    assert text_tree == tree_text_repr


def test_remove_child_failure(simple_lawtext_tree):
    """Test if removing a non-existing child node is handled properly."""

    with pytest.raises(ValueError) as execinfo:
        simple_lawtext_tree.remove_child(bulletpoint="(5)")
    assert str(execinfo.value) == "Child (5) not found"
