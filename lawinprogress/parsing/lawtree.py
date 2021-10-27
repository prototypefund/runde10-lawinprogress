"""Implementation of the specific tree to parse laws to."""
import regex as re
from anytree import NodeMixin, RenderTree
from natsort import natsorted


class LawTextNode(NodeMixin):
    """Data sctructure to represent a node in anytree.

    Used for parsing the source laws.
    """

    def __init__(self, text, bulletpoint, parent=None, children=None):
        self.text = text
        self.bulletpoint = bulletpoint
        self.parent = parent
        if children:  # set children only if given
            self.children = children

    def sort_children(self):
        """Sort the children in natural order."""
        self.children = natsorted(self.children, key=lambda node: node.bulletpoint)

    def insert_child(self, text: str, bulletpoint: str):
        """Insert a child for the node by bulletpoint and increment if necessary.

        The new node is added at the appropriate location (order) of the children of the node.
        If the node already exists (determined by bulletpoint) it will be inserted and the other
        nodes will be incremented.

        Args:
            text: Text of the newly created child node.
            bulletpoint: Bulletpoint of the newly created child node.
        """
        # find out where to insert
        other_bulletpoints = [child.bulletpoint for child in self.children]
        children = list(self.children)
        try:
            insert_index = other_bulletpoints.index(bulletpoint)
        except ValueError as err:
            insert_index = len(children)
        # insert the bulletpoint at the right place
        children.insert(
            insert_index,
            LawTextNode(
                text=text,
                bulletpoint=bulletpoint,
                parent=self,
            ),
        )
        self.children = tuple(children)

        # if duplicates, it means there are two children with the same bulletpoint and we should increment
        last_bulletpoint = None
        if len(set(node.bulletpoint for node in self.children)) < len(self.children):
            for node in self.children:
                if node.bulletpoint == last_bulletpoint:
                    # increment the bulletpoint
                    node.bulletpoint = _increment(node.bulletpoint)
                last_bulletpoint = node.bulletpoint
        # if there is nothing to increment, do nothing

    def remove_child(self, bulletpoint: str):
        """Remove a child from the node by bulletpoint match.

        Decrement following childrens bulletpoints if nessecary.

        Args:
            bulletpoint: Identifier string to the node.

        Raises:
            ValueError if the bulletpoint is not found.
        """
        # find the location to delete
        bulletpoints = [child.bulletpoint for child in self.children]
        try:
            removal_index = bulletpoints.index(bulletpoint)
        except ValueError as err:
            raise ValueError(f"Child {bulletpoint} not found")
        # remove the node
        self.children[removal_index].parent = None
        # decrement the following nodes
        for node in self.children[removal_index:]:
            node.bulletpoint = _decrement(node.bulletpoint)

    def __repr__(self):
        return "{} - {}".format(self.bulletpoint, self.text)

    def to_text(self):
        """return the full law text"""
        treestr = ""
        for pre, _, node in RenderTree(self):
            treestr += "{}{} {}\n".format(" " * len(pre), node.bulletpoint, node.text)
        return treestr

    def _print(self):
        for pre, _, node in RenderTree(self):
            treestr = "{}{} - {}".format(pre, node.bulletpoint, node.text)
            print(treestr.ljust(8))


def _increment(bulletpoint: str) -> str:
    """Function increment a bulletpoint string.

    Args:
        bulletpoint: string of the bulletpoint to increment.

    Returns:
        Incremented bulletpoint string.
    """

    # works only for numericals now...
    number = int("".join([char for char in bulletpoint if char.isdigit()]))
    # replace the numerical
    return re.sub(r"\d{1,3}", str(number + 1), bulletpoint)


def _decrement(bulletpoint: str) -> str:
    """Function decrement a bulletpoint string.

    Args:
        bulletpoint: string of the bulletpoint to increment.

    Returns:
        Decremented bulletpoint string.
    """

    # works only for numericals now...
    number = int("".join([char for char in bulletpoint if char.isdigit()]))
    # replace the numerical
    return re.sub(r"\d{1,3}", str(number - 1), bulletpoint)
