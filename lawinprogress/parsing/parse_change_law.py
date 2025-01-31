"""Functions to parse the change law from a line-by-line representation."""
import dataclasses
from typing import List

import regex as re

from lawinprogress.parsing.change_law_utils import preprocess_raw_law
from lawinprogress.parsing.lawtree import LawTextNode


@dataclasses.dataclass
class Change:
    """Class for storing a change request."""

    location: List[str]
    sentences: List[str]
    text: List[str]
    change_type: str
    raw_text: str

    @classmethod
    def fromdict(cls, asdict: dict):
        """Return an instance of a Change from a object dumped with dataclasses.asdict()."""
        return cls(**asdict)

    def todict(self):
        return dataclasses.asdict(self)


def parse_changes(
    change_law_text: str,
    law_title: str,
) -> List[Change]:
    """Wrapper function to parse and changes from the change law text.

    Args:
      change_law_text: Text of the change law.
      law_title: Title of the affected law.

    Returns:
      List of requested Changes.
    """
    # format the change requests and parse them to tree
    clean_change_law = preprocess_raw_law(change_law_text)
    parsed_change_law_tree = LawTextNode(text=law_title, bulletpoint="Titel:")
    parsed_change_law_tree = parse_change_law_tree(
        text=clean_change_law, source_node=parsed_change_law_tree
    )

    # parse the change requests in a structured line format
    all_change_lines = []
    # collect all paths to tree leaves and join them in the right order
    for leaf_node in parsed_change_law_tree.leaves:
        path = [str(leaf_node)]
        node = leaf_node
        while node.parent:
            node = node.parent
            path.append(str(node))
        change_line = " ".join(path[::-1][1:])
        all_change_lines.append(change_line)

    # parse the change request lines to changes
    change_requests = []
    for change_request_line in all_change_lines:
        res = parse_change_request_line(change_request_line)
        if res:
            change_requests.extend(res)
    return change_requests


def parse_change_law_tree(text: str, source_node: LawTextNode) -> LawTextNode:
    """Parse raw change law text into a structured format.

    Look for bullet point patters and build a tree with it.

    Args:
        text: raw text of the law.

    Returns:
        Structured output. A tree of LawTextNodes.
    """
    patterns = [
        r"^##",
        r"^\d{1,2}\.",
        r"^[a-z]\)",
        r"^[a-z][a-z]\)",
        r"^[a-z][a-z][a-z]\)",
        r"^\([a-z0-9]{1,3}\)",
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


def _adapt_change_location_for_source_law(location: str) -> str:
    """Adapt a chnage law location string to fit the naming of locations in the source law.

    Args:
        location: String of a change law location identifier.

    Returns:
        A string representing a location identifier in a source law.
    """
    # replace some text bulletpoints to match the bulletpoints in the source laws
    if location.startswith("Absatz "):
        location = location.replace("Absatz ", "(") + ")"
    elif location.startswith("Abs. "):
        location = location.replace("Abs. ", "(") + ")"
    elif location.startswith("Nummer "):
        location = location.replace("Nummer ", "") + "."
    elif location.startswith("Nr. "):
        location = location.replace("Nr. ", "") + "."
    elif location.startswith("Buchstabe "):
        location = location.replace("Buchstabe ", "") + ")"
    return location


def parse_change_location(line: str) -> List[str]:
    """Parse the location identifiers from one line of change request.

    Find the location identifiers (i.e. Absatz, § 4, etc) in the text and return these.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        List of strings, every string is one step of the location to change.
    """
    location_identifiers = [
        r"Inhaltsübersicht",
        r"Kapitel\s*\d{1,3}",
        r"§\s+\d{1,3}[a-z]?",
        r"Überschrift",
        r"Absatz\s+\d{1,3}[a-z]?",
        r"Abs.\s+\d{1,3}",
        r"Nummer\s+\d{1,3}",
        r"Nr.\s+\d{1,3}",
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
    # and adapt the location to match the bulletpoint patterns used in the source law
    return [
        _adapt_change_location_for_source_law(re.sub(r"\s+", " ", loc))
        for loc in location
    ]


def parse_change_sentences(line: str) -> List[str]:
    """Parse the affected sentences identifiers from one line of change request.

    Find the sentence identifiers (i.e. Satz 5, Sätze 7 bis 9, etc) in the text and return these.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        List of strings, every string is a sentence to change.
    """
    sentence_identifiers = [
        r"(Satz|Sätze)\s+\d{1,3}(\s+(bis|und)(\s+)?(Satz|Sätze)?(\s+)?\d{1,3})?",
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
        line[m.span()[0] : m.span()[1]]
        .replace("Komma", " ,")
        .replace("Semikolon", " ;")
        .replace("Punkt", " .")
        .strip()
        for m in re.finditer(
            r"((?<=„)(.|\n)*?(?=“)|Komma|Semikolon|Punkt)", line, re.MULTILINE
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
    raw_line = line
    # if the change is of type "Absatz 7 wird Absatz 8" skip here.
    renumbering = False
    regex_str_singular = r"(Absatz|Abs.|Paragraph|Nummer|Nr.)\s(\d{1,2}|[a-z]{1,2}\)?)\swird\s(Absatz|Abs.|Paragraph|Nummer|Nr.)\s(\d{1,2}|[a-z]{1,2}\)?)"
    regex_str_multiple = r"(Absatz|Absätze|Abätze|Paragraph|Nummern)\s(\d{1,2}|[a-z]{1,2}\)?)\s(bis|und)\s(\d{1,2}|[a-z]{1,2}\)?)\swerden\s(der|die|das)?\s?(Absatz|Absätze|Abätze|Paragraph|Nummern)\s(\d{1,2}|[a-z]{1,2}\)?)\s(bis|und)\s(\d{1,2}|[a-z]{1,2}\)?)"
    if re.search(regex_str_singular, line) or re.search(regex_str_multiple, line):
        renumbering = True
    line = re.sub(regex_str_singular, "", line)
    line = re.sub(regex_str_multiple, "", line)

    changes = []  # could be multiple changes in one line; right now we only allow one

    # TODO Move these to enumeration type and improt from there.
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
                    raw_text=raw_line,
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
                raw_text=raw_line,
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
                raw_text=raw_line,
            )
        ]
    return changes
