"""Main functiosn to apply changes to parsed source laws."""
import copy
from typing import List

from anytree import findall

from pre_law_viewer.apply_changes.edit_functions import (
    _delete_after,
    _insert_after,
    _rephrase,
    _replace,
)
from pre_law_viewer.parsing.parse_source_law import LawTextNode


def _find_path(location_list: List[str], parse_tree: LawTextNode) -> List[LawTextNode]:
    """Find path to node in the provided tree.
    
    Args:
        location_list: List of location identifiers that represent a path.
        parse_tree: A tree of LawTextNodes to collect the nodes on the path from.
    
    Returns:
        A list of LawTextNodes representing the path to the location.
    """
    path = []
    res = parse_tree
    for loc in location_list:
        if loc.startswith("Absatz "):
            loc = loc.replace("Absatz ", "(") + ")"
        elif loc.startswith("Nummer "):
            loc = loc.replace("Nummer ", "") + "."
        elif loc.startswith("Buchstabe "):
            loc = loc.replace("Buchstabe ", "") + ")"
        try:
            res = findall(res, filter_=lambda node: loc == node.bulletpoint)[0]
            path.append(res)
        except:
            # print("Location {} not found".format(loc))
            pass
    return path


def apply_changes(law_tree: LawTextNode, changes: dict) -> LawTextNode:
    """Apply the provided changes to the provided tree.
    
    Args:
        law_tree: A tree of LawTextNodes
        changes: A dict with changes, containing "location", "how" and "text" to specify the changes.
    
    Returns:
        Tree of LawTextNodes with the requested changes if we where able to apply them.
    """
    res_law_tree = copy.deepcopy(law_tree)
    for change in changes:
        path = _find_path(location_list=change["location"], parse_tree=res_law_tree)
        change_type = change["how"]
        if change_type == "replace":
            print("APPLIED {}:\n{}".format(change_type, change))
            res_law_tree = _replace(res_law_tree, path, change)
        elif change_type == "insert_after":
            print("APPLIED {}:\n{}".format(change_type, change))
            res_law_tree = _insert_after(res_law_tree, path, change)
        # elif change_type == "rephrase":
        #    print("APPLIED {}:\n{}".format(change_type, change))
        #    res_law_tree = _rephrase(res_law_tree, path, change)
        elif change_type == "delete_after":
            print("APPLIED {}:\n{}".format(change_type, change))
            res_law_tree = _delete_after(res_law_tree, path, change)
        else:
            print("SKIPPED {}:\n{}".format(change_type, change))
    return res_law_tree
