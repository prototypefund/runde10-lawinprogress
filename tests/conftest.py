"""Fixtures and setup for tests."""
import pytest

from lawinprogress.parsing.lawtree import LawTextNode


@pytest.fixture(scope="function")
def simple_lawtext_tree() -> LawTextNode:
    """Return a simple law text tree."""
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
    return tree
