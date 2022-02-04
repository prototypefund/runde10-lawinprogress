"""Main script to generate diffs from change law pdf.

Example usage:
    poetry run python ./lawinprogress/generate_diff.py -c data/0483-21.pdf --html
"""
import os
import logging
from typing import List, Tuple

import click
import outputformat as ouf
from anytree import PreOrderIter

from lawinprogress.apply_changes.apply_changes import ChangeResult, apply_changes
from lawinprogress.libdiff.html_diff import html_diffs
from lawinprogress.parsing.change_law_utils import preprocess_raw_law
from lawinprogress.parsing.lawtree import LawTextNode
from lawinprogress.parsing.parse_change_law import (
    Change,
    parse_change_law_tree,
    parse_change_request_line,
)
from lawinprogress.parsing.parse_source_law import parse_source_law
from lawinprogress.parsing.proposal_pdf_to_artikles import (
    extract_law_titles,
    extract_raw_proposal,
    extract_separate_change_proposals,
    read_pdf_law,
    remove_inkrafttreten,
)
from lawinprogress.source_law_api import (
    FuzzyLawSlugRetriever,
    get_source_law_rechtsinformationsportal,
)


def process_pdf(change_law_path: str) -> Tuple[List[str], List[str]]:
    """Wrapper function to process pdf of change law.

    Args:
      change_law_path: Path to the pdf in question.

    Returns:
      List of law titles affected by the change law.
      List of texts of the change requests.
    """
    # read the change law
    change_law_raw = read_pdf_law(change_law_path)

    # idenfify the different laws affected
    change_law_extract = extract_raw_proposal(change_law_raw)
    proposals_list = extract_separate_change_proposals(change_law_extract)
    law_titles = extract_law_titles(proposals_list)
    law_titles, proposals_list = remove_inkrafttreten(law_titles, proposals_list)
    return law_titles, proposals_list


def retrieve_source_law(search_title: str) -> List[dict]:
    """Retrieve the soruce law from the API."""
    slug = FuzzyLawSlugRetriever.fuzzyfind(search_title)
    logging.info(slug)

    if slug:
        return get_source_law_rechtsinformationsportal(slug)
    return None


def parse_and_apply_changes(
    change_law_text: str,
    source_law: List[dict],
    law_title: str,
) -> Tuple[LawTextNode, LawTextNode, List[Change], List[ChangeResult], int]:
    """Wrapper function to parse and apply changes from the change law text to a source law.

    Args:
      change_law_text: Text of the change law.
      source_law: Structured output of the rechtsinformationsportal API of the affected source law.
      law_title: Title of the affected law.

    Returns:
      Tree of LawTextNodes of the law before the changes applied.
      Tree of LawTextNodes of the law after the changes applied.
      List of requested Changes.
      List of change results.
      Number of successfully applied changes.
    """
    # format the change requests and parse them to tree
    clean_change_law = preprocess_raw_law(change_law_text)
    parsed_change_law_tree = LawTextNode(text=law_title, bulletpoint="change")
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

    # parse source law
    parsed_law_tree = parse_source_law(source_law, law_title=law_title)

    # apply changes to the source law
    res_law_tree, change_results, n_succesfull_applied_changes = apply_changes(
        parsed_law_tree,
        change_requests,
    )
    return (
        parsed_law_tree,
        res_law_tree,
        change_requests,
        change_results,
        n_succesfull_applied_changes,
    )


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
    help="Where to write the output (modified laws).",
    default="./output/",
)
@click.option(
    "--html",
    is_flag=True,
    help="If a html synopsis should be generated.",
)
def generate_diff(change_law_path: str, output_path: str, html: bool):
    """Generate the diff from the change law and the source law."""
    ouf.bigtitle("Welcome")
    ouf.bigtitle("to")
    ouf.bigtitle("Law in Progress")
    click.echo(ouf.boxtitle(f"Started parsing {change_law_path}", return_str=True))
    click.echo("\n" + "#" * 150 + "\n")

    # process the pdf
    law_titles, proposals_list = process_pdf(change_law_path)

    # parse and apply changes for every law that should be changed
    for law_title, change_law_text in zip(law_titles, proposals_list):
        # find and load the source law
        source_law = retrieve_source_law(law_title)
        if source_law:
            click.echo(f"Apply changes to {law_title}")
        else:
            click.echo(f"Cannot find source law {law_title}. SKIPPING")
            continue
        click.echo("\n" + "#" * 150 + "\n")

        # Parse the source and change law and apply the requested changes.
        (
            parsed_law_tree,
            res_law_tree,
            change_requests,
            change_results,
            n_succesfull_applied_changes,
        ) = parse_and_apply_changes(
            change_law_text,
            source_law,
            law_title,
        )

        # print a status update
        result_status = ouf.bar(
            n_succesfull_applied_changes,
            len(change_requests),
            style="block",
            length=15,
            title="Successfully applied changes",
            title_pad=15,
            return_str=True,
        )
        click.echo(result_status)

        #  save final version to file
        write_path = (
            f"{output_path}{law_title}_modified_{change_law_path.split('/')[-1]}.txt"
        )
        source_write_path = (
            f"{output_path}{law_title}_source_{change_law_path.split('/')[-1]}.txt"
        )
        click.echo(f"\n>> Write results to {write_path}")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with open(write_path, "w", encoding="utf8") as file:
            file.write(res_law_tree.to_text())
        with open(source_write_path, "w", encoding="utf8") as file:
            file.write(parsed_law_tree.to_text())

        if html:
            html_str = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Law in Progress</title>
  <link rel="stylesheet" href="../lawinprogress/templates/css/style.css">
</head>"""
            # generate a list of all applied changes in the order of the affected lines/nodes
            applied_change_results = [
                node.changes for node in PreOrderIter(res_law_tree) if node.changes
            ]
            # get the diff
            html_side_by_side = html_diffs(
                parsed_law_tree.to_text(),
                res_law_tree.to_text(),
                applied_change_results,
            )
            html_str += html_side_by_side
            # save to fiel
            diff_write_path = (
                f"{output_path}{law_title}_diff_{change_law_path.split('/')[-1]}.html"
            )
            with open(diff_write_path, "w", encoding="utf8") as file:
                file.write(html_str)

        click.echo("\n" + "#" * 150 + "\n")
    click.echo("DONE.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    generate_diff()
