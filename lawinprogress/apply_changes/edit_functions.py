"""Functions to apply the different edits requested in the change laws."""
from typing import List

import regex as re

from lawinprogress import NLP
from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import Change
from lawinprogress.parsing.parse_source_law import parse_source_law_tree

BULLETPOINT_PATTERNS = [
    r"^Kapitel\s*\d{1,3}",
    r"^§\s*\d{1,3}[a-z]?",
    r"^\d{1,3}\.",
    r"^\([a-z0-9]{1,3}\)",
    r"^[a-z]{1,2}\)",
]


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
        return "{}:\n\tlocation={}\n\tsentences={}\n\ttext={}\n\tstatus={}\n".format(
            self.message,
            self.change.location,
            self.change.sentences,
            self.change.text,
            self.status
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
    if len(change.text) == 2 and len(change.sentences) == 0:
        node.text = node.text.replace(
            __clean_text(change.text[0]), __clean_text(change.text[1])
        )
    elif len(change.text) == 1 and len(change.sentences) > 0:
        # replace the sentences in question by the change text.
        sentences = __split_text_to_sentences(node.text)
        sentence_numbers = re.findall(r"\d{1,3}", change.sentences[0])
        if "bis" in change.sentences[0]:
            # sentence range
            sentences[
                int(sentence_numbers[0]) - 1 : int(sentence_numbers[1]) - 1
            ] = __clean_text(change.text[0].strip())
        elif "und" in change.sentences[0]:
            # multiple sentences
            msg = "Replace with multiple sentences 'und' and one text is currently not supported."
            return ChangeResult(change, node, 0, msg)
        else:
            # single sentence
            sentences[int(sentence_numbers[0]) - 1] = __clean_text(
                change.text[0].strip()
            )
        node.text = " ".join(sentences)
    elif len(change.text) == 2 and len(change.sentences) > 0:
        # replace the text in the sentence in question.
        sentences = __split_text_to_sentences(node.text)
        sentence_numbers = re.findall(r"\d{1,3}", change.sentences[0])
        if "bis" in change.sentences[0]:
            # sentence range
            sentences[
                int(sentence_numbers[0]) - 1 : int(sentence_numbers[1]) - 1
            ] = __clean_text(change.text[0].strip())
        elif "und" in change.sentences[0]:
            # multiple sentences
            sentences[int(sentence_numbers[0]) - 1] = __clean_text(
                change.text[0].strip()
            )
            sentences[int(sentence_numbers[1]) - 1] = __clean_text(
                change.text[1].strip()
            )
        else:
            # single sentence
            sentences[int(sentence_numbers[0]) - 1] = sentences[
                int(sentence_numbers[0]) - 1
            ].replace(change.text[0], change.text[1])
        node.text = " ".join(sentences)
    else:
        msg = "Not enougth text to replace."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status=1)


def _insert_after(node: LawTextNode, change: Change) -> ChangeResult:
    """Insert text after a given text or section.

    Assumes list of change.text to be of even length, uneven positions are the location
    # after which to insert, even positions are the text to insert.
    """
    if len(change.text) == 0:
        msg = "Failed to insert after! Not enougth text found."
        # return status 0
        return ChangeResult(change, node, 0, msg)

    bulletpoint_matches = [
        re.match(pattern, change.text[0]) for pattern in BULLETPOINT_PATTERNS
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
            msg = "Insert with sentence range 'bis' is currently not supported."
            return ChangeResult(change, node, 0, msg)
        if "und" in change.sentences[0]:
            msg = "Insert with multiple sentences 'und' is currently not supported."
            return ChangeResult(change, node, 0, msg)
        # single sentence
        number = re.findall(r"\d{1,3}", change.sentences[0])[0]
        sentences.insert(int(number), __clean_text(change.text[0].strip()))
        node.text = " ".join(sentences)
    else:
        msg = "Failed to insert after! Unknown reason!"
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status=1)


def _rephrase(node: LawTextNode, change: Change) -> ChangeResult:
    """Rephrase the text in the specific location."""
    if len(change.text) == 1 and len(change.sentences) == 0:
        # remove leading bulletpoints if there are any
        change_text = change.text[0]
        for pattern in BULLETPOINT_PATTERNS:
            change_text = re.sub(pattern, "", change_text, count=1)
        # apply the change
        node.text = __clean_text(change_text.strip())
    elif len(change.text) == 1 and len(change.sentences) == 1:
        # if there is a sentence description, only rephrase that location
        # remove leading bulletpoints if there are any
        change_text = change.text[0]
        for pattern in BULLETPOINT_PATTERNS:
            change_text = re.sub(pattern, "", change_text, count=1)
        # apply the change
        sentences = __split_text_to_sentences(node.text)
        if "bis" in change.sentences[0]:
            msg = "Rephrase with sentence range 'bis' is currently not supported."
            return ChangeResult(change, node, 0, msg)
        if "und" in change.sentences[0]:
            msg = "Rephrase with multiple sentences 'und' is currently not supported."
            return ChangeResult(change, node, 0, msg)
        # single sentence
        number = re.findall(r"\d{1,3}", change.sentences[0])[0]
        sentences[int(number) - 1] = __clean_text(change_text.strip())
        node.text = " ".join(sentences)
    else:
        msg = "Failed to rephrase! Too much or too little texts."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status=1)


def _append(node: LawTextNode, change: Change) -> ChangeResult:
    """Add given text after the given location."""
    if len(change.text) == 1:
        change_text = change.text[0]
        bulletpoint_matches = [
            re.match(pattern, change_text) for pattern in BULLETPOINT_PATTERNS
        ]
        if any(bulletpoint_matches):
            # if starts with bulletpoint insert directly into the tree
            match = [m for m in bulletpoint_matches if m][0]
            bulletpoint_match = change_text[match.span()[0] : match.span()[1]]
            node.insert_child(
                text=change_text[match.span()[1] + 1 :],
                bulletpoint=bulletpoint_match,
            )
        else:
            node.text = node.text + " " + __clean_text(change_text)
    else:
        msg = "Failed to append! To much texts."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status=1)


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
    if len(change.text) == 0 and len(change.sentences) == 0:
        try:
            node.parent.remove_child(bulletpoint=node.bulletpoint)
        except AttributeError as err:
            msg = f"Failed to cancel! Node has no parent. {err}"
            return ChangeResult(change, node, 0, msg)
    elif len(change.text) == 0 and len(change.sentences) == 1:
        # remove the sentences in question
        sentences = __split_text_to_sentences(node.text)
        sentence_numbers = re.findall(r"\d{1,3}", change.sentences[0])
        if "bis" in change.sentences[0]:
            # sentence range
            del sentences[int(sentence_numbers[0]) - 1 : int(sentence_numbers[1]) - 1]
            node.text = " ".join(sentences)
        elif "und" in change.sentences[0]:
            # multiple sentences
            for num in sentence_numbers[::-1]:
                sentences.pop(int(num) - 1)
            node.text = " ".join(sentences)
        else:
            # single sentence
            sentences.pop(int(sentence_numbers[0]) - 1)
            node.text = " ".join(sentences)
        node.text = " ".join(sentences)
    else:
        msg = "Failed to cancel! Text present."
        return ChangeResult(change, node, 0, msg)
    return ChangeResult(change, node, status=1)
