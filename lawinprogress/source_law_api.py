"""Classes and functions to get and handle source laws from rechtsinformationsportal."""
import json
import os
from functools import lru_cache
from itertools import chain
from typing import List

import requests

from rapidfuzz import fuzz, process

SOURCE_LAW_LOOKUP_PATH = "./data/source_laws/rechtsinformationsportalAPI.json"


@lru_cache(maxsize=16)
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
        local_path = f"./data/source_laws/laws/{slug}.json"
        if os.path.isfile(local_path):
            with open(local_path, "r", encoding="utf8") as local_law:
                law_json = json.load(local_law)
        else:
            api_response = requests.get(
                f"https://api.rechtsinformationsportal.de/v1/laws/{slug}?include=contents"
            )
            if api_response.status_code != 200:
                return []
            law_json = api_response.json()
    except requests.exceptions.RequestException as ex:
        raise SystemExit(ex)

    contents = law_json["data"]["contents"]

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
            with open(SOURCE_LAW_LOOKUP_PATH, "r", encoding="utf8") as lookup_json:
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
    @lru_cache(maxsize=128)
    def fuzzyfind(cls, search_title: str) -> str:
        """Run fuzzy matching on the title string and return the top result."""
        lookup_dict = cls.get_lookup()
        result = process.extractOne(search_title, list(lookup_dict.keys()), scorer=fuzz.QRatio)
        return lookup_dict.get(result[0], None)
