"""Functions and classes to parse the source law into a tree."""
from typing import List

import anytree
import regex as re

from lawinprogress.parsing.lawtree import LawTextNode

HTML_PATTERN = re.compile(r"<.*?>")


def clean_up_structured_string(string: str) -> str:
    """Remove table structure and replace by appropriate newlines for parsing."""
    # remove footnote links
    string = re.sub(r"<SUP.*?SUP\>", "", string)

    # remove other structured tags
    string = re.sub(r"<DL.*?>", "", string)
    string = re.sub(r"</DL>", "", string)
    strings = [
        substr.replace("</LA></DD>", "") for substr in re.split(r"</DT>|<DT>", string)
    ]
    return "\n".join([re.sub(r"<DD.*?>|<LA.*?>", "", substr) for substr in strings])


def parse_source_law(source_law: List[dict], law_title: str) -> LawTextNode:
    """Parse the API response to LawTextNodes."""
    # TODO: Parse Inhaltsübersicht

    # create the source node
    source_law_tree = LawTextNode(text=law_title, bulletpoint="Titel:")
    source_law_tree._id = None

    for law_item in source_law:
        # find the parent node
        parent_node = anytree.search.findall(
            source_law_tree,
            filter_=lambda node: node._id == law_item["parent"]["id"]
            if (hasattr(node, "_id") and law_item["parent"])
            else False,
        )
        if parent_node:
            parent_node = parent_node[0]
        # prepare the text for the new node content
        try:
            # TODO: enable 'Inhaltsübersicht'
            if law_item.get("name") == "Inhaltsübersicht":
                law_text = "None"
            else:
                law_text = law_item.get("title") + " " + law_item.get("body")
        except TypeError:
            if law_item.get("title"):
                law_text = law_item.get("title")
            elif law_item.get("body"):
                law_text = law_item.get("body")
            else:
                law_text = ""

        # if the text body contains more structure, parse it here
        if law_text and (law_text.count("<P>") > 1 or "<DL" in law_text):
            law_text = law_text.replace("<P>", "\n").replace("</P>", "")
            new_node = LawTextNode(
                text=law_item.get("title", ""),
                bulletpoint=law_item["name"],
                parent=parent_node if parent_node else source_law_tree,
            )

            _ = parse_source_law_tree(
                text=clean_up_structured_string(law_text), source_node=new_node
            )
        else:
            # else just clean and add a new node
            law_text = HTML_PATTERN.sub("", law_text) if law_text else "(weggefallen)"

            new_node = LawTextNode(
                text=law_text,
                bulletpoint=law_item["name"],
                parent=parent_node if parent_node else source_law_tree,
            )
        new_node._id = law_item["id"]
    return source_law_tree


def parse_source_law_tree(text: str, source_node: LawTextNode) -> LawTextNode:
    """Parse raw law text into a structured format.

    Look for bullet point patters and build a tree with it.

    Args:
        text: raw text of the law.

    Returns:
        Structured output. A tree of LawTextNodes.
    """
    patterns = [
        r"\nKapitel\s*\d{1,3}",
        r"\n§\s*\d{1,3}[a-z]?",
        r"\n\s*\([a-z0-9]{1,3}\)",
        r"\n\s*\d{1,2}\.",
        r"\n\s*\d{1,2}[a-z]{1,2}\.",
        r"\n\s*[a-z]\)",
    ]

    # build the tree
    for pattern in patterns:
        used_texts = []
        # search the pattern in the text
        if re.search(pattern, text):
            split_text = re.split(pattern, text)
            for idx, match in enumerate(re.finditer(pattern, text)):
                new_node = LawTextNode(
                    text=HTML_PATTERN.sub(
                        "", re.split("|".join(patterns), split_text[idx + 1].strip())[0]
                    ),
                    # store the text for this bullet point on this level
                    bulletpoint=text[match.span()[0] : match.span()[1]].strip(),
                    # apply the function recursively to get all levels
                    parent=source_node,
                )
                # get the next level associated with this node
                _ = parse_source_law_tree(split_text[idx + 1], source_node=new_node)
                # store the text already used to remove later. Store bulletpoint and text
                used_texts.append(
                    text[match.span()[0] : match.span()[1]] + split_text[idx + 1]
                )
        # if parsing has happened for a piece of text, we remove it.
        for used_text in used_texts:
            text = text.replace(used_text, "")
    return source_node
