"""Main functiosn to apply changes to parsed source laws."""
import copy
from typing import List, Tuple

import click
from anytree import findall

from lawinprogress.apply_changes.edit_functions import (
    ChangeResult,
    _append,
    _cancelled,
    _delete_after,
    _insert_after,
    _rephrase,
    _replace,
)
from lawinprogress.parsing.parse_change_law import Change
from lawinprogress.parsing.parse_source_law import LawTextNode


def _log_change(result_text: str, change: Change, loglevel: int = 1):
    """Convinience function to log a change application."""
    if loglevel == 0:
        click.echo(f"{result_text} {change.change_type}")
    elif loglevel == 1:
        click.echo(
            "{} {}:\n\tlocation={}\n\tsentences={}\n\ttext={}\n".format(
                result_text,
                change.change_type,
                change.location,
                change.sentences,
                change.text,
            )
        )
    elif loglevel == 2:
        click.echo(
            "{} {}:\n\tlocation={}\n\tsentences={}\n\ttext={}\n\traw_text={}\n".format(
                result_text,
                change.change_type,
                change.location,
                change.sentences,
                change.text,
                change.raw_text,
            )
        )
    else:
        raise ValueError("Unknown loglevel in change logging.")


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
        # if we have a special location like Überschrift, just return the current_node
        if location in ["Überschrift"]:
            return current_node

        # find the node in question in the tree
        search_result = findall(
            current_node, filter_=lambda node: location == node.bulletpoint
        )
        if len(search_result) == 0:
            # no path found
            # print(f"Location {location} not found.")
            return None
        if len(search_result) == 1:
            # exactly one path found; as it should be
            current_node = search_result[0]
        else:
            # more than one path found; should not happen - Stop here
            # print(f"Multiple paths to location {location} found. Stopping.")
            return None

    return current_node


def apply_changes(
    law_tree: LawTextNode, changes: List[Change], loglevel: int = 1
) -> Tuple[LawTextNode, List[ChangeResult], int]:
    """Apply the provided changes to the provided tree.

    Args:
        law_tree: A tree of LawTextNodes
        changes: A dict with changes, containing "location", "how" and "text"
                 to specify the changes.
        loglevel: How detailed should the logs be? Integer between 0 and 2.

    Returns:
        Tree of LawTextNodes with the requested changes if we where able to apply them.
        List of change results and the number of successfully applied changes.
    """
    res_law_tree = copy.deepcopy(law_tree)
    change_results = []
    n_succesfull_applied_changes = 0
    for change in changes:
        try:
            # find the node that needs to be changed
            if (
                change.text
                and change.text[0].startswith(change.location[-1])
                and change.change_type == "append"
            ):
                # if the node is appended but doesnt exist jet
                # dont use the last part of the location
                node = _find_node(
                    location_list=change.location[:-1], parse_tree=res_law_tree
                )
            else:
                # just find the node
                node = _find_node(
                    location_list=change.location, parse_tree=res_law_tree
                )

            # store the representation of the tree to compare it with the tree after the change
            tree_text_before = res_law_tree.to_text()
            # if we found no path, we skip
            if not node:
                _log_change("SKIPPING. No unique path found for", change, loglevel)
                continue
            change_type = change.change_type
            if change_type == "replace":
                change_result = _replace(node, change)
            elif change_type == "insert_after":
                change_result = _insert_after(node, change)
            elif change_type == "rephrase":
                change_result = _rephrase(node, change)
            elif change_type == "append":
                change_result = _append(node, change)
            elif change_type == "delete_after":
                change_result = _delete_after(node, change)
            elif change_type == "cancelled":
                change_result = _cancelled(node, change)
            elif change_type == "RENUMBERING":
                _log_change("SKIPPED", change, loglevel)
                # we skip it because the insertion code in Treelawnode should handle all of this
                n_succesfull_applied_changes += 1
            else:
                _log_change("SKIPPED", change, loglevel)
                continue
            if res_law_tree.to_text() != tree_text_before:
                # if something changed, then we successfully applied something
                _log_change("APPLIED", change, loglevel)
                n_succesfull_applied_changes += change_result.status
            else:
                # if nothign changed, we should be informed
                if change_type not in ["RENUMBERING", "MULTIPLE_CHANGES", "UNKNOWN"]:
                    _log_change("APPLIED WITHOUT CHANGE", change, loglevel)
                    continue
            node.changes.append(change_result)
            change_results.append(change_result)
        except Exception as err:
            print(f"\nERROR: {err}")
            print(change)
            print("\n")
    return res_law_tree, change_results, n_succesfull_applied_changes
