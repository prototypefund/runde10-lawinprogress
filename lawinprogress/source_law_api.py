"""Functions to get and handle source laws"""
from typing import List

import requests


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
