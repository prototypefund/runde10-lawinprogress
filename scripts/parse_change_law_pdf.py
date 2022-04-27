"""Script to parse a change law to a structured representation of the changes as a json file.

Example usage:
    poetry run python ./scripts/parse_change_law_pdf.py -c data/0483-21.pdf
"""
import os

import json
import click
import outputformat as ouf
from anytree import PreOrderIter

from lawinprogress.parsing.parse_change_law import parse_changes
from lawinprogress.processing.proposal_pdf_to_artikles import process_pdf


@click.command()
@click.option(
    "change_law_path",
    "-c",
    help="Path to the change law pdf.",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "output_path",
    "-o",
    help="Where to write the output json.",
    default="./output/",
)
def parse_change_law_pdf(change_law_path: str, output_path: str):
    """Parse the change law pdf and save it as structured json"""
    ouf.bigtitle("Welcome")
    ouf.bigtitle("to")
    ouf.bigtitle("Law in Progress")
    click.echo(ouf.boxtitle(f"Started parsing {change_law_path}", return_str=True))
    click.echo("\n" + "#" * 150 + "\n")

    # process the pdf
    law_titles, proposals_list, full_law_title = process_pdf(change_law_path)

    # parse and apply changes for every law that should be changed
    for law_title, change_law_text in zip(law_titles, proposals_list):
        # parse changes
        change_requests = parse_changes(change_law_text, law_title)

        # print a status update
        click.echo(f"Found {len(change_requests)} changes.")

        # create a dict of all changes
        changes = [change.todict() for change in change_requests]

        #  save final version to file
        write_path = (
            f"{output_path}changes_to_{law_title}_{change_law_path.split('/')[-1]}.json"
        )
        click.echo(f"\n>> Write results to {write_path}")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with open(write_path, "w", encoding="utf8") as file:
            file.write(json.dumps(changes, ensure_ascii=False))

        click.echo("\n" + "#" * 150 + "\n")
    click.echo("DONE.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    parse_change_law_pdf()
