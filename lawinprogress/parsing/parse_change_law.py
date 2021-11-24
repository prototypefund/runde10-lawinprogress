"""Functions to parse the change law from a line-by-line representation."""
from dataclasses import dataclass
from typing import List

import regex as re

from lawinprogress.parsing.lawtree import LawTextNode


@dataclass  # (frozen=True)
class Change:
    """Class for storing a change request."""

    location: List[str]
    sentences: List[str]
    text: List[str]
    change_type: str


def parse_change_law_tree(text: str, source_node: LawTextNode) -> LawTextNode:
    """Parse raw change law text into a structured format.

    Look for bullet point patters and build a tree with it.

    Args:
        text: raw text of the law.

    Returns:
        Structured output. A tree of LawTextNodes.
    """
    patterns = [
        r"^\d{1,2}\.",
        r"^[a-z]\)",
        r"^[a-z][a-z]\)",
        r"^\([a-z0-9]\)",
    ]
    # build the tree
    for pattern in patterns:
        used_texts = []
        regex_pattern = re.compile(pattern, re.MULTILINE)
        # search the pattern in the text
        if regex_pattern.search(text):
            # split the text at the found pattern
            split_text = regex_pattern.split(text)
            # create new nodes from the matches
            for idx, match in enumerate(regex_pattern.finditer(text)):
                new_node = LawTextNode(
                    text=split_text[idx + 1].strip().split("\n")[0],
                    # store the text for this bullet point on this level
                    bulletpoint=text[match.span()[0] : match.span()[1]].strip(),
                    # add the node to the tree
                    parent=source_node,
                )
                # get the next level associated with this node
                _ = parse_change_law_tree(split_text[idx + 1], source_node=new_node)
                used_texts.append(split_text[idx + 1])
        # if parsing has happened for a piece of text, we remove it.
        for used_text in used_texts:
            text = text.replace(used_text, "")
    return source_node


def parse_change_location(line: str) -> List[str]:
    """Parse the location identifiers from one line of change request.

    Find the location identifiers (i.e. Absatz, § 4, etc) in the text and return these.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        List of strings, every string is one step of the location to change.
    """
    location_identifiers = [
        r"Inhaltsübersicht?",
        r"§\s+\d{1,3}[a-z]?",
        r"Überschrift",
        r"Absatz\s+\d{1,3}",
        r"Nummer\s+\d{1,3}",
        r"Buchstabe\s+[a-z]",
    ]

    location = []
    for loc_ident in location_identifiers:
        try:
            # search location identifier in text
            location.extend(
                re.search(
                    loc_ident,
                    re.sub(
                        r"(?<=„)(.|\n)*?(?=“)", "", line
                    ),  # don't search in quoted text
                ).captures()
            )
        except:
            # if the identifier is not found, pass
            pass
    # return a list of locations, but replace any multiple whitespace as a single whitespace
    return [re.sub(r"\s+", " ", loc) for loc in location]


def parse_change_sentences(line: str) -> List[str]:
    """Parse the affected sentences identifiers from one line of change request.

    Find the sentence identifiers (i.e. Satz 5, Sätze 7 bis 9, etc) in the text and return these.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        List of strings, every string is a sentence to change.
    """
    sentence_identifiers = [
        r"(Satz|Sätze)\s\d{1,3}(\s(bis|und)\s?(Satz|Sätze)?\s?\d{1,3})?",
    ]

    sentences = []
    for sent_ident in sentence_identifiers:
        try:
            # search location identifier in text
            sentences.extend(
                re.search(
                    sent_ident,
                    re.sub(
                        r"(?<=„)(.|\n)*?(?=“)", "", line
                    ),  # don't search in quoted text
                ).captures()
            )
        except:
            # if the identifier is not found, pass
            pass
    return sentences


def parse_change_text(line: str) -> List[str]:
    """Parse the text that needs to be changed from one line of change request.

    Look for text in quotation marks and return it.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        List of strings, every string is one change text.
    """
    return [
        line[m.span()[0] : m.span()[1]].replace("Komma", ",").replace("Semikolon", ";")
        for m in re.finditer(
            r"((?<=„)(.|\n)*?(?=“)|Komma|Semikolon)", line, re.MULTILINE
        )
    ]


def parse_change_request_line(line: str) -> List[Change]:
    """Parse the actions of one line of change requests.

    Look for certain keywords in the line (i.e. "eingefügt", "gestrichen", etc)
    to identify what should be done in this change.
    Then parse change location and change text.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        A list of Changes with required changes extracted from this line.
    """
    # if the change is of type "Absatz 7 wird Absatz 8" skip here.
    renumbering = False
    regex_str_singular = r"(Absatz|Paragraph|Nummer)\s(\d{1,2}|[a-z]{1,2}\)?)\swird\s(Absatz|Paragraph|Nummer)\s(\d{1,2}|[a-z]{1,2}\)?)"
    regex_str_multiple = r"(Absatz|Absätze|Abätze|Paragraph|Nummern)\s(\d{1,2}|[a-z]{1,2}\)?)\s(bis|und)\s(\d{1,2}|[a-z]{1,2}\)?)\swerden\s(der|die|das)?\s?(Absatz|Absätze|Abätze|Paragraph|Nummern)\s(\d{1,2}|[a-z]{1,2}\)?)\s(bis|und)\s(\d{1,2}|[a-z]{1,2}\)?)"
    if re.search(regex_str_singular, line) or re.search(regex_str_multiple, line):
        renumbering = True
    line = re.sub(regex_str_singular, "", line)
    line = re.sub(regex_str_multiple, "", line)

    changes = []  # could be multiple changes in one line; right now we only allow one

    # TODO Tobias: Move these to enumeration type and improt from there.
    keyword_type_pairs = [
        ("eingefügt", "insert_after"),
        ("ersetzt", "replace"),
        ("gefasst", "rephrase"),
        ("angefügt", "append"),
        ("gestrichen", "delete_after"),
        ("aufgehoben", "cancelled"),
        ("vorangestellt", "prepend"),
    ]

    # parse change location and change text
    location = parse_change_location(line)
    sentences = parse_change_sentences(line)
    change_text = parse_change_text(line)
    # determine the type of change
    for keyword, change_type in keyword_type_pairs:
        if keyword in line:
            changes.append(
                Change(
                    location=location,
                    sentences=sentences,
                    text=change_text,
                    change_type=change_type,
                )
            )
    if len(changes) == 0:
        # We assume every line is a change, so if nothing is found,
        # we don't know yet how to handle it.
        changes.append(
            Change(
                location=location,
                sentences=sentences,
                text=change_text,
                change_type="RENUMBERING" if renumbering else "UNKNOWN",
            )
        )
    elif len(changes) > 1:
        # we only allow one change per line for now
        # if multiple changes present, we
        changes = [
            Change(
                location=location,
                sentences=sentences,
                text=change_text,
                change_type="MULTIPLE_CHANGES",
            )
        ]
    return changes
