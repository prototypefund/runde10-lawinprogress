"""Functions to apply the different edits requested in the change laws."""
from typing import List

import regex as re

from lawinprogress.parsing.parse_source_law import LawTextNode


def _replace(
    law_tree: LawTextNode, path: List[LawTextNode], change: dict
) -> LawTextNode:
    # apply replace operation to the last text in the path
    if len(change["text"]) == 2:
        path[-1].text = path[-1].text.replace(change["text"][0], change["text"][1])
    else:
        print("not enougth text to replace")
    return law_tree


def _insert_after(
    law_tree: LawTextNode, path: List[LawTextNode], change: dict
) -> LawTextNode:
    # insert text after a given text
    # assumes list of change["text"] to be of even length, uneven positions are the location
    # after which to insert, even positions are the text to insert.
    if len(change["text"]) % 2 == 0:
        for idx in range(len(change["text"]) // 2):
            path[-1].text = re.sub(
                r"\b{}\b".format(change["text"][2 * idx]),
                change["text"][2 * idx] + " " + change["text"][2 * idx + 1],
                path[-1].text,
            )
    elif len(change["text"]) == 1 and any(
        [
            re.match(r"^\d\.", change["text"][0]),
            re.match(r"^[a-z]\)", change["text"][0]),
            re.match(r"^[a-z][a-z]\)", change["text"][0]),
            re.match(r"^\([a-z1-9]\)", change["text"][0]),
        ]
    ):
        # if there is only one text to insert and
        # it starts with a bulletidentifier add a new node to the tree
        _ = LawTextNode(
            text=change["text"][0], bulletpoint="(new)", parent=path[-1].parent
        )
    else:
        print("Failed to insert after! Not enought texts.")
    return law_tree


def _rephrase(
    law_tree: LawTextNode, path: List[LawTextNode], change: dict
) -> LawTextNode:
    return law_tree


def _delete_after(
    law_tree: LawTextNode, path: List[LawTextNode], change: dict
) -> LawTextNode:
    if len(change["text"]) == 1:
        path[-1].text = path[-1].text.replace(change["text"][0], "")
    elif len(change["text"]) > 1:
        path[-1].text = path[-1].text.replace("".join(change["text"][1:]), "")
    else:
        print("Failed to delete! Not enought text.")
    return law_tree
