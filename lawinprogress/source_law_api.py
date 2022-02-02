"""Classes and functions to get and handle source laws from rechtsinformationsportal."""
import json
from itertools import chain
from typing import List

import requests
from thefuzz import process

SOURCE_LAW_LOOUP_PATH = "./data/source_laws/rechtsinformationsportalAPI.json"


def get_source_law_rechtsinformationsportal(slug: str) -> List[dict]:
    """Call the rechtsinformationsportal API.

    Using their slug law identifier
    return a list of dictionaries each with the type, date, name, title, parent, body, and footnotes
    this can correspond to our tree structure later on.

    Args:
        slug: String of the reqested law's shortcode.

    Returns:
        List of dicts containing different parts of the requested law.
    """
    try:
        api_response = requests.get(
            f"https://api.rechtsinformationsportal.de/v1/laws/{slug}?include=contents"
        )
    except requests.exceptions.RequestException as ex:
        raise SystemExit(ex)

    contents = api_response.json()["data"]["contents"]

    return_keys = {
        "type",
        "id",
        "name",
        "title",
        "parent",
        "body",
        "footnotes",
    }
    return [{key: item[key] for key in return_keys if key in item} for item in contents]


class FuzzyLawSlugRetriever:
    """Class to act as a singleton to fuzzy retrieve slugs by law titles."""

    lookup = None

    @classmethod
    def get_lookup(cls) -> dict:
        """Get the lookup dict for this instance, loading it if it's not already loaded."""
        if cls.lookup is None:
            with open(SOURCE_LAW_LOOUP_PATH, "r", encoding="utf8") as lookup_json:
                source_laws_raw = json.load(lookup_json)
                source_laws = list(chain(*source_laws_raw))
                cls.lookup = {
                    law["titleShort"]: law["slug"]
                    for law in source_laws
                    if law["titleShort"]
                } | {
                    law["titleLong"]: law["slug"]
                    for law in source_laws
                    if law["titleLong"]
                }
        return cls.lookup

    @classmethod
    def fuzzyfind(cls, search_title: str) -> str:
        """Run fuzzy matching on the title string and return the top result."""
        lookup_dict = cls.get_lookup()
        result = process.extractOne(search_title, list(lookup_dict.keys()))
        return lookup_dict.get(result[0], None)
