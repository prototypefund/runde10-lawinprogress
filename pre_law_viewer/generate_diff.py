"""Main script to generate diffs from pairs (change law pdf, source law text).

Example usage:
    poetry run python ./pre_law_viewer/generate_diff.py -c data/0483-21.pdf -s data/0483-21_wettbewerbsgesetzt.txt
"""
import click
from pre_law_viewer.parsing.change_law_utils import read_pdf_law, preprocess_raw_law, expand_text
from pre_law_viewer.parsing.parse_change_law import parse_change_request_line
from pre_law_viewer.parsing.parse_source_law import parse_source_law_tree, LawTextNode
from pre_law_viewer.apply_changes.apply_changes import apply_changes


@click.command()
@click.option('change_law_path', '-c', help='Path to the change law pdf.', type=click.Path(exists=True))
@click.option('source_law_path', '-s', help='Path to the source law txt.', type=click.Path(exists=True))
def generate_diff(change_law_path, source_law_path):
    """Generate the diff from the change law and the source law."""
    click.echo("Started parsing {}".format(change_law_path))
    # 1. read and format the change requests
    change_law_raw = read_pdf_law(change_law_path)
    clean_change_law = preprocess_raw_law(change_law_raw)
    clean_text = expand_text(clean_change_law)
    
    # 2 parse the change requests in a structured format
    change_requests = []
    for change_request_line in clean_text.split("\n"):
        res = parse_change_request_line(change_request_line)
        change_requests.extend(res)
        
    # 3. load and parse source law
    source_law_text = open(source_law_path, "r").read()
    parsed_law_tree = parse_source_law_tree(
        text=source_law_text
    )
    
    # 4 apply changes to the source law
    res_law_tree = apply_changes(parsed_law_tree, change_requests)

    # 5. save final version to file
    with open('output.txt', 'w') as f:
        f.write(res_law_tree._to_text())
    click.echo("DONE.")
    
    
if __name__ == '__main__':
    generate_diff()