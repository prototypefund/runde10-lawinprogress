"""Main script to generate diffs from change law pdf.

Example usage:
    poetry run python ./lawinprogress/generate_diff.py -c data/0483-21.pdf
"""
import os

import click

from lawinprogress.apply_changes.apply_changes import apply_changes
from lawinprogress.parsing.change_law_utils import expand_text, preprocess_raw_law
from lawinprogress.parsing.parse_change_law import parse_change_request_line
from lawinprogress.parsing.parse_source_law import parse_source_law_tree
from lawinprogress.parsing.proposal_pdf_to_artikles import (
    extract_law_titles,
    extract_raw_proposal,
    extract_seperate_change_proposals,
    read_pdf_law,
    remove_inkrafttreten,
)


@click.command()
@click.option(
    "change_law_path",
    "-c",
    help="Path to the change law pdf.",
    type=click.Path(exists=True),
)
@click.option(
    "output_path",
    "-o",
    help="Where to write the output (logs and modified laws).",
    default="./output/",
)
def generate_diff(change_law_path, output_path):
    """Generate the diff from the change law and the source law."""
    click.echo("Started parsing {}".format(change_law_path))
    # read the change law
    change_law_raw = read_pdf_law(change_law_path)

    # idenfify the different laws affected
    change_law_extract = extract_raw_proposal(change_law_raw)
    proposals_list = extract_seperate_change_proposals(change_law_extract)
    law_titles = extract_law_titles(proposals_list)
    law_titles, proposals_list = remove_inkrafttreten(law_titles, proposals_list)

    # parse and apply changes for every law that should be changed
    for law_title, change_law in zip(law_titles, proposals_list):
        # find and load the source law
        source_law_path = "data/source_laws/{}.txt".format(law_title)
        try:
            with open(source_law_path, "r") as file:
                source_law_text = file.read()
            click.echo("Apply changes to {}".format(law_title))
        except:
            click.echo("Cannot find source law {}. SKIPPING".format(law_title))
            continue

        # format the change requests
        clean_change_law = preprocess_raw_law(change_law)
        clean_text = expand_text(clean_change_law)

        # parse the change requests in a structured format
        change_requests = []
        for change_request_line in clean_text.split("\n"):
            res = parse_change_request_line(change_request_line)
            change_requests.extend(res)

        # parse source law

        parsed_law_tree = parse_source_law_tree(text=source_law_text)

        # apply changes to the source law
        res_law_tree = apply_changes(parsed_law_tree, change_requests)

        #  save final version to file
        write_path = "{}{}_modified_{}.txt".format(
            output_path, law_title, change_law_path.split("/")[-1]
        )
        click.echo("Write results to {}".format(write_path))
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with open(write_path, "w") as file:
            file.write(res_law_tree.to_text())
    click.echo("DONE.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    generate_diff()
