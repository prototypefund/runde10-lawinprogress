"""Main functiosn to apply changes to parsed source laws."""
import copy
import logging
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

logger = logging.getLogger(__name__)


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
            if current_node.bulletpoint.startswith("Kapitel"):
                return current_node
            return None
        if len(search_result) == 1:
            # exactly one path found; as it should be
            current_node = search_result[0]
        else:
            # more than one path found; should not happen - Stop here
            return None

    return current_node


def apply_changes(
    law_tree: LawTextNode,
    changes: List[Change],
) -> Tuple[LawTextNode, List[ChangeResult], int]:
    """Apply the provided changes to the provided tree.

    Args:
        law_tree: A tree of LawTextNodes
        changes: A dict with changes, containing "location", "how" and "text"
                 to specify the changes.

    Returns:
        Tree of LawTextNodes with the requested changes if we where able to apply them.
        List of change results and the number of successfully applied changes.
    """
    res_law_tree = copy.deepcopy(law_tree)
    change_results = []
    n_succesfull_applied_changes = 0
    for change in changes:
        logger.info(change)
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
                change_result = ChangeResult(
                    change, None, status=0, message="SKIPPING. No unique path found for"
                )
                logger.info(change_result)
                change_results.append(change_result)
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
                # we skip it because the insertion code in Treelawnode should handle all of this
                change_result = ChangeResult(
                    change, node, status=1, message="RENUMBERING"
                )
                n_succesfull_applied_changes += 1
            else:
                change_result = ChangeResult(change, node, status=0, message="SKIPPED")
            if res_law_tree.to_text() != tree_text_before:
                # if something changed, then we successfully applied something
                n_succesfull_applied_changes += change_result.status
            else:
                # if nothign changed, we should be informed
                if change_type not in ["RENUMBERING", "MULTIPLE_CHANGES", "UNKNOWN"]:
                    change_result = ChangeResult(
                        change, node, status=1, message="APPLIED WITHOUT CHANGE"
                    )
            node.changes.append(change_result)
            change_results.append(change_result)
            logger.info(change_result)
        except IndexError as err:
            logger.warning(f"\nERROR: {err}")
            logger.warning(change)
    return res_law_tree, change_results, n_succesfull_applied_changes
