"""Main script to generate an updated version of the source law due to a change law pdf.

Example usage:
    poetry run python ./scripts/generate_updated_version.py -c data/0483-21.pdf
"""
import os

import click
import outputformat as ouf
from anytree import PreOrderIter

from lawinprogress.apply_changes.apply_changes import apply_changes
from lawinprogress.parsing.parse_change_law import parse_changes
from lawinprogress.parsing.parse_source_law import parse_source_law
from lawinprogress.processing.proposal_pdf_to_artikles import process_pdf
from lawinprogress.processing.source_law_retrieval import retrieve_source_law


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
def generate_updated_version(change_law_path: str, output_path: str):
    """Generate the diff from the change law and the source law."""
    ouf.bigtitle("Welcome")
    ouf.bigtitle("to")
    ouf.bigtitle("Law in Progress")
    click.echo(ouf.boxtitle(f"Started parsing {change_law_path}", return_str=True))
    click.echo("\n" + "#" * 150 + "\n")

    # process the pdf
    law_titles, proposals_list, full_law_title = process_pdf(change_law_path)

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
        # parse source law
        parsed_law_tree = parse_source_law(source_law, law_title=law_title)

        # parse changes
        change_requests = parse_changes(change_law_text, law_title)

        # apply changes to the source law
        res_law_tree, change_results, n_succesfull_applied_changes = apply_changes(
            parsed_law_tree,
            change_requests,
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

        click.echo("\n" + "#" * 150 + "\n")
    click.echo("DONE.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    generate_updated_version()
