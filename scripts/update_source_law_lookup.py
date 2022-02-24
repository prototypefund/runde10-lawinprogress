"""Script to update the lookup json for source law shortcodes.

Example usage:
    poetry run python ./scripts/update_source_law_lookup.py
"""
import json

import click
import requests


@click.command()
def update_source_law_lookup():
    """Main function."""
    click.echo("Started retrieving new version of shortcode lookup.")
    source_url = "https://api.rechtsinformationsportal.de/v1/laws?include=all_fields"

    # retrieve lookup
    Ri_response = [requests.get(source_url)]
    next_page = Ri_response[-1].json()["links"]["next"]
    while next_page != None:
        Ri_response.append(requests.get(next_page))
        next_page = Ri_response[-1].json()["links"]["next"]
        x += 1

    rechtsinformationsportal_list = [
        (Ri_response[page].json()["data"]) for page in range(0, x + 1)
    ]

    # save to file
    save_path = "./data/source_laws/rechtsinformationsportalAPI.json"
    with open(save_path, "w") as file:
        json.dump(rechtsinformationsportal_list, file)
    echo.click(f"Save file to {save_path}")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    update_source_law_lookup()
