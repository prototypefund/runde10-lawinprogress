"""Main script to generate diffs from change law pdf.

Example usage:
    poetry run python ./lawinprogress/generate_diff.py -c data/0483-21.pdf
"""
import os

import click

from lawinprogress.apply_changes.apply_changes import apply_changes
from lawinprogress.parsing.change_law_utils import preprocess_raw_law
from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import (
    parse_change_law_tree,
    parse_change_request_line,
)
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
    help="Where to write the output (modified laws).",
    default="./output/",
)
@click.option(
    "loglevel",
    "-l",
    help="How details should logs be. Integer from 0 to 2.",
    type=int,
    default=1,
)
def generate_diff(change_law_path: str, output_path: str, loglevel: int):
    """Generate the diff from the change law and the source law."""
    click.echo("Started parsing {}".format(change_law_path))
    click.echo("\n" + "#" * 150 + "\n")
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
            with open(source_law_path, "r", encoding="utf8") as file:
                source_law_text = file.read()
            click.echo("Apply changes to {}".format(law_title))
        except Exception as err:
            click.echo("Cannot find source law {}. SKIPPING".format(law_title))
            continue

        click.echo("\n" + "#" * 150 + "\n")

        # format the change requests and parse them to tree
        clean_change_law = preprocess_raw_law(change_law)
        parsed_change_law_tree = LawTextNode(text=law_title, bulletpoint="change")
        parsed_change_law_tree = parse_change_law_tree(
            text=clean_change_law, source_node=parsed_change_law_tree
        )

        # parse the change requests in a structured line format
        all_change_lines = []
        # collect all paths to tree leaves and join them in the right order
        for leave_node in parsed_change_law_tree.leaves:
            path = [str(leave_node)]
            node = leave_node
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

        # parse source law
        parsed_law_tree = LawTextNode(text="law_title", bulletpoint="source")
        parsed_law_tree = parse_source_law_tree(
            text=source_law_text, source_node=parsed_law_tree
        )

        # apply changes to the source law
        res_law_tree = apply_changes(parsed_law_tree, change_requests, loglevel)

        #  save final version to file
        write_path = "{}{}_modified_{}.txt".format(
            output_path, law_title, change_law_path.split("/")[-1]
        )
        source_write_path = "{}{}_source_{}.txt".format(
            output_path, law_title, change_law_path.split("/")[-1]
        )
        click.echo("Write results to {}".format(write_path))
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with open(write_path, "w", encoding="utf8") as file:
            file.write(res_law_tree.to_text())
        with open(source_write_path, "w", encoding="utf8") as file:
            file.write(parsed_law_tree.to_text())
        click.echo("\n" + "#" * 150 + "\n")
    click.echo("DONE.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    generate_diff()
