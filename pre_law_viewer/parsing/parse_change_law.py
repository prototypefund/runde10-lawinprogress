"""Functions to parse the change law from a line-by-line representation."""
from typing import List, Tuple

import regex as re


def parse_change_location(line: str) -> List[str]:
    """Parse the location identifiers from one line of change request.

    Find the location identifiers (i.e. Absatz, § 4, Satz 5, etc) in the text and return these.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        List of strings, every string is one step of the location to change.
    """
    location_identifiers = [
        r"Inhaltsübersicht?",
        r"§ \d{1,3}[a-z]?",
        r"Überschrift",
        r"Absatz \d{1,3}",
        r"Satz \d{1,3}",
        r"Nummer \d{1,3}",
        r"Buchstabe [a-z]",
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
    return location


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


def parse_change_request_line(line: str) -> List[dict]:
    """Parse the actions of one line of change requests.

    Look for certain keywords in the line (i.e. "eingefügt", "gestrichen", etc) to identify what should be done in this change.
    Then parse change location and change text.

    Args:
        line: One line of text. Contains exactly one change request.

    Returns:
        A list of dicts with required changes extracted from this line.
    """
    res = []
    if "eingefügt" in line:
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "insert_after",
        }
        res.append(res_dict)
    elif "ersetzt" in line:
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "replace",
        }
        res.append(res_dict)
    elif "gefasst" in line:
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "rephrase",
        }
        res.append(res_dict)
    elif "angefügt" in line:
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "append",
        }
        res.append(res_dict)
    elif "gestrichen" in line:
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "delete_after",
        }
        res.append(res_dict)
    elif "aufgehoben" in line:
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "cancelled",
        }
        res.append(res_dict)
    else:
        # We assume every line is a change, so if nothing is found, we don't know yet how to handle it.
        res_dict = {
            "location": parse_change_location(line),
            "text": parse_change_text(line),
            "how": "UNKNOWN",
        }
        res.append(res_dict)

    return res
