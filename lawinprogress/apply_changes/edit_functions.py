"""Functions to apply the different edits requested in the change laws."""
from typing import List

import regex as re

from lawinprogress import NLP
from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import Change
from lawinprogress.parsing.parse_source_law import parse_source_law_tree


class ChangeResult:
    """Store the result of a change application."""

    def __init__(
        self,
        change: Change,
        affected_node: LawTextNode,
        status: int,
        message: str = "Applied edit",
    ):
        self.change = change
        self.affected_node = affected_node
        self.status = status
        self.message = message

    def __repr__(self) -> str:
        return "{}:\n\tlocation={}\n\tsentences={}\n\ttext={}\n".format(
            self.change.change_type,
            self.change.location,
            self.change.sentences,
            self.change.text,
        )


def __split_text_to_sentences(text: str) -> List[str]:
    """Split a text into sentences.

    Uses spacy and improves upon.
    """
    sentences = []
    sent_text = ""
    for sent in NLP(text).sents:
        # join sentences is split by BGBl.
        sent_text += sent.text
        if not sent.text.endswith("BGBl."):
            sentences.append(sent_text)
            sent_text = ""
    return [sent for sent in sentences if sent.strip()]


def __clean_text(text: str) -> str:
    """Remove unnecessary whitespaces.

    Use only when needed and not by default.
    """
    return " ".join(token for token in text.split(" ") if token)


def _replace(node: LawTextNode, change: Change) -> ChangeResult:
    """Replace text in the node."""
    status = 1
    if len(change.text) == 2:
        node.text = node.text.replace(
            __clean_text(change.text[0]), __clean_text(change.text[1])
        )
    else:
        msg = "not enougth text to replace"
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status)


def _insert_after(node: LawTextNode, change: Change) -> ChangeResult:
    """Insert text after a given text or section.

    Assumes list of change.text to be of even length, uneven positions are the location
    # after which to insert, even positions are the text to insert.
    """
    status = 1  # return value to determain failure or success.

    if len(change.text) == 0:
        msg = "Failed to insert after! Not enougth text found."
        # return status 0
        return ChangeResult(change, node, 0, msg)

    bulletpoint_matches = [
        re.match(pattern, change.text[0])
        for pattern in [
            r"^Kapitel\s*\d{1,3}",
            r"^\d\.",
            r"^§\s\d{1,3}[a-z]?",
            r"^[a-z]\)",
            r"^[a-z][a-z]\)",
            r"^\([a-z1-9]\)",
        ]
    ]

    if len(change.text) % 2 == 0:
        for idx in range(len(change.text) // 2):
            node.text = re.sub(
                r"\b{}\b".format(change.text[2 * idx]),
                change.text[2 * idx] + " " + change.text[2 * idx + 1],
                node.text,
            )
    elif len(change.text) == 1 and any(bulletpoint_matches):
        # find the first match (there should only be one)
        match = [m for m in bulletpoint_matches if m][0]
        bulletpoint_match = change.text[0][match.span()[0] : match.span()[1]]

        # find the root node
        root = node
        while root.parent:
            root = root.parent
        # if there is only one text to insert and
        # it starts with a bulletidentifier add a new node to the tree
        if bulletpoint_match in [child.bulletpoint for child in node.parent.children]:
            node.parent.insert_child(
                text=change.text[0][match.span()[1] + 1 :],
                bulletpoint=bulletpoint_match,
            )
        elif bulletpoint_match in [child.bulletpoint for child in root.children]:
            root.insert_child(
                text=change.text[0][match.span()[1] + 1 :],
                bulletpoint=bulletpoint_match,
            )
        else:
            # if there is more
            # parse the change text and insert it in the tree
            # replace 4 whitepsaces by newline
            change_text = change.text[0].replace(4 * " ", "\n")
            for child in node.parent.children:
                change_text = change_text.replace(
                    "\n" + child.bulletpoint, " " + child.bulletpoint
                )
            change_text = "\n" + change_text
            _ = parse_source_law_tree(text=change_text, source_node=node.parent)
            node.parent.sort_children()
    elif len(change.text) == 1 and len(change.sentences) == 1:
        # insert after a specific sentence
        sentences = __split_text_to_sentences(node.text)
        if "bis" in change.sentences[0]:
            pass
        elif "und" in change.sentences[0]:
            pass
        else:
            # single sentence
            number = re.findall(r"\d{1,3}", change.sentences[0])[0]
            sentences.insert(int(number), __clean_text(change.text[0].strip()))
            node.text = " ".join(sentences)
    else:
        msg = "Failed to insert after! Unknown reason!"
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status)


def _rephrase(node: LawTextNode, change: Change) -> ChangeResult:
    """Rephrase the text in the specific location."""
    status = 1
    if len(change.text) == 1 and len(change.sentences) == 0:
        # remove leading bulletpoints if there are any
        change_text = change.text[0]
        for pattern in [
            r"^\(\d{1,2}\)",
            r"^\d{1,2}\,",
            r"^[a-z]\)",
            r"^[a-z][a-z]\)",
            r"^\([a-z0-9]\)",
        ]:
            change_text = re.sub(pattern, "", change_text, count=1)
        # apply the change
        node.text = __clean_text(change_text.strip())
    elif len(change.text) == 1 and len(change.sentences) == 1:
        # if there is a sentence description, only rephrase that location
        # remove leading bulletpoints if there are any
        change_text = change.text[0]
        for pattern in [
            r"^\(\d{1,2}\)",
            r"^\d{1,2}\,",
            r"^[a-z]\)",
            r"^[a-z][a-z]\)",
            r"^\([a-z0-9]\)",
        ]:
            change_text = re.sub(pattern, "", change_text, count=1)
        # apply the change
        sentences = __split_text_to_sentences(node.text)
        if "bis" in change.sentences[0]:
            pass
        elif "und" in change.sentences[0]:
            pass
        else:
            # single sentence
            number = re.findall(r"\d{1,3}", change.sentences[0])[0]
            sentences[int(number) - 1] = __clean_text(change_text.strip())
            node.text = " ".join(sentences)
    else:
        msg = "Failed to rephrase! Too much or too little texts."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status)


def _append(node: LawTextNode, change: Change) -> ChangeResult:
    """Add given text after the given location."""
    status = 1
    if len(change.text) == 1:
        node.text = node.text + " " + __clean_text(change.text[0])
    else:
        msg = "Failed to append! To much texts."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status)


def _delete_after(node: LawTextNode, change: Change) -> ChangeResult:
    """Delete some text at the requested location."""
    status = 1
    if len(change.text) == 1:
        # If only one string in text, then delete that string from
        # the respective source law location.
        node.text = node.text.replace(change.text[0].replace("  ", " "), "").replace(
            "  ", " "
        )
    elif len(change.text) > 1:
        # if more than one string in text, replace all following texts.
        node.text = node.text.replace(
            " ".join(change.text[1:]).replace("  ", " "), ""
        ).replace("  ", " ")
    else:
        msg = "Failed to delete! Not enought text."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status)


def _cancelled(node: LawTextNode, change: Change) -> ChangeResult:
    """Remove the node in question from the tree."""
    status = 1
    if len(change.text) == 0 and len(change.sentences) == 0:
        try:
            node.parent.remove_child(bulletpoint=node.bulletpoint)
        except AttributeError as err:
            print("Failed to cancel! Node has no parent")
            status = 0
    elif len(change.text) == 0 and len(change.sentences) == 1:
        # remove the sentences in question
        sentences = __split_text_to_sentences(node.text)
        if "bis" in change.sentences[0]:
            # sentence range
            numbers = re.findall(r"\d{1,3}", change.sentences[0])
            del sentences[int(numbers[0]) - 1 : int(numbers[1]) - 1]
            node.text = " ".join(sentences)
        elif "und" in change.sentences[0]:
            # multiple sentences
            numbers = re.findall(r"\d{1,3}", change.sentences[0])
            for num in numbers[::-1]:
                sentences.pop(int(num) - 1)
            node.text = " ".join(sentences)
        else:
            # single sentence
            number = re.findall(r"\d{1,3}", change.sentences[0])[0]
            sentences.pop(int(number) - 1)
            node.text = " ".join(sentences)
        node.text = " ".join(sentences)
    else:
        msg = "Failed to cancel! Text present."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status)
