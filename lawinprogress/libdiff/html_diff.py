"""Contains functions to generate a side-by-side diff/synopsis in html."""
import difflib
import html
from itertools import zip_longest
from typing import Callable, List, Tuple, Union

from lawinprogress.apply_changes.edit_functions import ChangeResult

from .diffhelpers import align_seqs, sentencize, tokenize, untokenize


class MarkupConfig:
    """Store the config for the html markup."""

    left_text_background = "#ff5631"
    left_section_background = "#ffcbbd"
    right_text_background = "#2ea769"
    right_section_background = "#c8f0da"
    change_section_background = "#F0EDE6"


def mark_text(tokens: List[str], colorcode: str) -> List[str]:
    """Put html background color on a span of text."""
    if len(tokens) > 0:
        tokens[0] = (
            f'<span style="background: {colorcode};border-radius: 3px;">' + tokens[0]
        )
        tokens[-1] += "</span>"
    return tokens


def markup_diff(
    seq_a: List[str],
    seq_b: List[str],
    mark: Callable[List[str], List[str]],
    isjunk: Union[None, Callable[[str], bool]] = None,
) -> Tuple[List[str], List[str]]:
    """Returns a and b with any differences processed by mark

    Junk is ignored by the differ
    """
    default_mark = lambda x: x
    seqmatcher = difflib.SequenceMatcher(
        isjunk=isjunk, a=seq_a, b=seq_b, autojunk=False
    )
    out_a, out_b = [], []
    for tag, idx_a0, idx_a1, idx_b0, idx_b1 in seqmatcher.get_opcodes():
        out_a += (
            default_mark(seq_a[idx_a0:idx_a1])
            if tag == "equal"
            else mark(seq_a[idx_a0:idx_a1], colorcode=MarkupConfig.left_text_background)
        )
        out_b += (
            default_mark(seq_b[idx_b0:idx_b1])
            if tag == "equal"
            else mark(
                seq_b[idx_b0:idx_b1], colorcode=MarkupConfig.right_text_background
            )
        )
    assert len(out_a) == len(seq_a)
    assert len(out_b) == len(seq_b)
    return out_a, out_b


def html_sidebyside(
    left_text: List[str],
    right_text: List[str],
    change_results: List[List[ChangeResult]],
) -> str:
    """Create a side-by-side div-table for the diff/synopsis."""
    # html headers
    out = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Law in Progress</title>
</head>"""
    # page title
    out += f'<center><h2>{left_text[0].split("source ")[-1]}</h2></center>'
    # TODO: show not applied changes
    # prepare successfull changes
    success_changes = [
        [change_result for change_result in results if change_result.status != 0]
        for results in change_results
        if results
    ]
    # create the three column layout
    out += '<div style="padding: 50px;display: grid;grid-template-columns: auto auto auto;grid-column-gap: 40px;grid-row-gap: 0px;font-family:DejaVu Sans Mono;">'
    # make it align nicely
    out += "<p></p><p></p><p></p>"
    out += "<h3><center>Änderungsbefehl</center></h3><h3><center>alte Fassung</center></h3><h3><center>neue Fassung</center></h3>"
    change_idx = 0
    for left, right in zip_longest(left_text[1:], right_text[1:], fillvalue=""):
        left_leading_ws = len(left) - len(left.lstrip()) - 5
        right_leading_ws = len(right) - len(right.lstrip()) - 5
        left = left_leading_ws * "&nbsp;" + left.strip()
        right = right_leading_ws * "&nbsp;" + right.strip()
        if "<span" in left or "<span" in right:
            try:
                out += '<div style="background: {};padding: 2px;">{}</div>'.format(
                    MarkupConfig.change_section_background,
                    "<br><hr>".join(
                        [res.change.raw_text for res in success_changes[change_idx]]
                    ),
                )
                change_idx += 1
            except IndexError as err:
                out += f'<div style="background: {MarkupConfig.change_section_background};padding: 2px;">Something went wrong: {str(err)}</div>'

            out += f'<div style="background: {MarkupConfig.left_section_background};padding: 2px;">{left}</div>'
            out += f'<div style="background: {MarkupConfig.right_section_background};padding: 2px;">{right}</div>'
        else:
            out += f'<div style="background: {MarkupConfig.change_section_background};padding: 2px;"></div>'
            out += f'<div style="padding: 2px;">{left}</div>'
            out += f'<div style="padding: 2px;">{right}</div>'
    return out


def html_diffs(
    text_a: str, text_b: str, change_results: List[List[ChangeResult]]
) -> str:
    """Main function to get the side-by-side diff of two strings in html."""
    text_a = html.escape(text_a)
    text_b = html.escape(text_b)

    out_a, out_b = [], []
    for sent_a, sent_b in zip(*align_seqs(sentencize(text_a), sentencize(text_b))):
        mark_a, mark_b = markup_diff(tokenize(sent_a), tokenize(sent_b), mark=mark_text)
        out_a.append(untokenize(mark_a))
        out_b.append(untokenize(mark_b))

    return html_sidebyside(out_a, out_b, change_results)
