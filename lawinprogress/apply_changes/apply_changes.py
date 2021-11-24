"""Main functiosn to apply changes to parsed source laws."""
import copy
from typing import List

from anytree import findall

from lawinprogress.apply_changes.edit_functions import (
    _append,
    _cancelled,
    _delete_after,
    _insert_after,
    _rephrase,
    _replace,
)
from lawinprogress.parsing.parse_change_law import Change
from lawinprogress.parsing.parse_source_law import LawTextNode


def _adapt_change_location_for_source_law(location: str) -> str:
    """Adapt a chnage law location string to fit the naming of locations in the source law.

    Args:
        location: String of a change law location identifier.

    Returns:
        A string representing a location identifier in a source law.
    """
    # replace some text bulletpoints to match the bulletpoints in the source laws
    if location.startswith("Absatz "):
        location = location.replace("Absatz ", "(") + ")"
    elif location.startswith("Nummer "):
        location = location.replace("Nummer ", "") + "."
    elif location.startswith("Buchstabe "):
        location = location.replace("Buchstabe ", "") + ")"
    return location


def _find_node(location_list: List[str], parse_tree: LawTextNode) -> List[LawTextNode]:
    """The node by location in the provided tree.

    Args:
        location_list: List of location identifiers that represent a path to a node.
        parse_tree: A tree of LawTextNodes to collect the nodes on the path from.

    Returns:
        The LawTextNode found at the end of the path to the location.
    """
    current_node = parse_tree
    for location in location_list:
        # find the node in question in the tree
        search_result = findall(
            current_node, filter_=lambda node: location == node.bulletpoint
        )
        if len(search_result) == 0:
            # no path found
            print("Location {} not found.".format(location))
            return None
        elif len(search_result) == 1:
            # exactly one path found; as it should be
            current_node = search_result[0]
        else:
            # more than one path found; should not happen - Stop here
            print("Multiple paths to location {} found. Stopping.".format(location))
            return None

    return current_node


def apply_changes(law_tree: LawTextNode, changes: List[Change]) -> LawTextNode:
    """Apply the provided changes to the provided tree.

    Args:
        law_tree: A tree of LawTextNodes
        changes: A dict with changes, containing "location", "how" and "text"
                 to specify the changes.

    Returns:
        Tree of LawTextNodes with the requested changes if we where able to apply them.
    """
    res_law_tree = copy.deepcopy(law_tree)
    n_succesfull_applied_changes = 0
    for change in changes:
        status = 0
        # change location identifiers from the change law format to the source law format
        location_list = [
            _adapt_change_location_for_source_law(location)
            for location in change.location
        ]
        # find the node that needs to be changed
        node = _find_node(location_list=location_list, parse_tree=res_law_tree)
        # store the representation of the node to compare it with the node after the change
        node_text_before = node.to_text()
        # if we found no path, we skip
        if not node:
            print("No path found in {}. SKIPPING".format(change))
            continue
        change_type = change.change_type
        if change_type == "replace":
            status = _replace(node, change)
        elif change_type == "insert_after":
            status = _insert_after(node, change)
        elif change_type == "rephrase":
            status = _rephrase(node, change)
        elif change_type == "append":
            status = _append(node, change)
        elif change_type == "delete_after":
            status = _delete_after(node, change)
        elif change_type == "cancelled":
            status = _cancelled(node, change)
        elif change_type == "RENUMBERING":
            print("SKIPPED {}: {}".format(change_type, change))
            # we skip it because the insertion code in Treelawnode should handle all of this
            status = 1
        else:
            print("SKIPPED {}: {}".format(change_type, change))
        if node.to_text() != node_text_before:
            # if something changed, then we successfully applied something
            print("APPLIED {}: {}".format(change_type, change))
            n_succesfull_applied_changes += status
        else:
            # if nothign changed, we should be informed
            if change_type != "RENUMBERING":
                print("WITHOUT CHANGE {}: {}".format(change_type, change))
    # print a status update
    print(
        "\nSuccessfully applied {} out of {} changes ({:.1%})\n".format(
            n_succesfull_applied_changes,
            len(changes),
            n_succesfull_applied_changes / len(changes),
        )
    )
    return res_law_tree
