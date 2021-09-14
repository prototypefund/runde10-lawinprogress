"""Main functiosn to apply changes to parsed source laws."""
import copy
import regex as re
from typing import List
from anytree import findall
from pre_law_viewer.parsing.parse_source_law import LawTextNode
from pre_law_viewer.apply_changes.edit_functions import _replace, _insert_after, _rephrase, _delete_after


def _find_path(location_list: List[str], parse_tree: LawTextNode) -> List[LawTextNode]:
    # find path to node
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
        #elif change_type == "rephrase":
        #    print("APPLIED {}:\n{}".format(change_type, change))
        #    res_law_tree = _rephrase(res_law_tree, path, change)
        elif change_type == "delete_after":
            print("APPLIED {}:\n{}".format(change_type, change))
            res_law_tree = _delete_after(res_law_tree, path, change)
        else:
            print("SKIPPED {}:\n{}".format(change_type, change))
    return res_law_tree