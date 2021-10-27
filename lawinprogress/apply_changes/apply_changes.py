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


def _find_node(location_list: List[str], parse_tree: LawTextNode) -> List[LawTextNode]:
    """The node by location in the provided tree.

    Args:
        location_list: List of location identifiers that represent a path to a node.
        parse_tree: A tree of LawTextNodes to collect the nodes on the path from.

    Returns:
        The LawTextNode found at the end of the path to the location.
    """
    current_node = parse_tree
    for loc in location_list:
        # replace some text bulletpoints to match the bulletpoints in the source laws
        if loc.startswith("Absatz "):
            loc = loc.replace("Absatz ", "(") + ")"
        elif loc.startswith("Nummer "):
            loc = loc.replace("Nummer ", "") + "."
        elif loc.startswith("Buchstabe "):
            loc = loc.replace("Buchstabe ", "") + ")"

        # find the node in question in the tree
        search_result = findall(
            current_node, filter_=lambda node: loc == node.bulletpoint
        )
        if len(search_result) == 0:
            # no path found
            print("Location {} not found.".format(loc))
            return None
        elif len(search_result) == 1:
            # exactly one path found; as it should be
            current_node = search_result[0]
        else:
            # more than one path found; should not happen - Stop here
            print("Multiple paths to location {} found. Stopping.".format(loc))
            return None

    return current_node


def apply_changes(law_tree: LawTextNode, changes: List[Change]) -> LawTextNode:
    """Apply the provided changes to the provided tree.

    Args:
        law_tree: A tree of LawTextNodes
        changes: A dict with changes, containing "location", "how" and "text" to specify the changes.

    Returns:
        Tree of LawTextNodes with the requested changes if we where able to apply them.
    """
    res_law_tree = copy.deepcopy(law_tree)
    n_succesfull_applied_changes = 0
    for change in changes:
        status = 0
        # find the node that needs to be changed
        node = _find_node(location_list=change.location, parse_tree=res_law_tree)
        # if we found no path, we skip
        if not node:
            print("No path found in {}. SKIPPING".format(change))
            continue
        change_type = change.change_type
        if change_type == "replace":
            print("APPLIED {}: {}".format(change_type, change))
            status = _replace(node, change)
        elif change_type == "insert_after":
            print("APPLIED {}: {}".format(change_type, change))
            status = _insert_after(node, change)
        elif change_type == "rephrase":
            print("APPLIED {}:\n{}".format(change_type, change))
            status = _rephrase(node, change)
        elif change_type == "append":
            print("APPLIED {}:\n{}".format(change_type, change))
            status = _append(node, change)
        elif change_type == "delete_after":
            print("APPLIED {}: {}".format(change_type, change))
            status = _delete_after(node, change)
        elif change_type == "cancelled":
            print("APPLIED {}: {}".format(change_type, change))
            status = _cancelled(node, change)
        elif change_type == "RENUMBERING":
            print("SKIPPED {}: {}".format(change_type, change))
            # we skip it because the insertion code in Treelawnode should handle all of this
            status = 1
        else:
            print("SKIPPED {}: {}".format(change_type, change))
        n_succesfull_applied_changes += status
    # print a status update
    print(
        "\nSuccessfully applied {} out of {} changes ({:.1%})\n".format(
            n_succesfull_applied_changes,
            len(changes),
            n_succesfull_applied_changes / len(changes),
        )
    )
    return res_law_tree
