"""Contains functions to generate a side-by-side diff/synopsis in html."""
import difflib
import html
from itertools import zip_longest
from typing import Callable, List, Tuple, Union

import regex as re

from .diffhelpers import align_seqs, sentencize, tokenize, unsentencise, untokenize


class MarkupConfig:
    """Store the config for the html markup."""

    left_text_background = "#ff5631"
    left_section_background = "#ffcbbd"
    right_text_background = "#2ea769"
    right_section_background = "#c8f0da"


def mark_text(tokens: List[str], colorcode: str) -> List[str]:
    """Put html background color on a span of text."""
    if len(tokens) > 0:
        tokens[0] = (
            f'<span style="background: {colorcode};border-radius: 3px;">' + tokens[0]
        )
        tokens[-1] += "</span>"
    return tokens


def markup_diff(
    a: List[str],
    b: List[str],
    mark: Callable[List[str], List[str]],
    isjunk: Union[None, Callable[[str], bool]] = None,
) -> Tuple[List[str], List[str]]:
    """Returns a and b with any differences processed by mark

    Junk is ignored by the differ
    """
    default_mark = lambda x: x
    seqmatcher = difflib.SequenceMatcher(isjunk=isjunk, a=a, b=b, autojunk=False)
    out_a, out_b = [], []
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        out_a += (
            default_mark(a[a0:a1])
            if tag == "equal"
            else mark(a[a0:a1], colorcode=MarkupConfig.left_text_background)
        )
        out_b += (
            default_mark(b[b0:b1])
            if tag == "equal"
            else mark(b[b0:b1], colorcode=MarkupConfig.right_text_background)
        )
    assert len(out_a) == len(a)
    assert len(out_b) == len(b)
    return out_a, out_b


def html_sidebyside(a: List[str], b: List[str]) -> str:
    """Create a side-by-side div-table for the diff/synopsis."""
    # Set the panel display
    out = f'<center><h2>{a[0].split("source ")[-1]}</h2></center>'
    out += '<div style="padding: 50px;display: grid;grid-template-columns: 1fr 1fr;grid-column-gap: 70px;grid-row-gap: 1px;font-family:DejaVu Sans Mono;">'
    # There's some CSS in Jupyter notebooks that makes the first pair unalign. This is a workaround
    out += "<p></p><p></p>"
    for left, right in zip_longest(a[1:], b[1:], fillvalue=""):
        left_leading_ws = len(left) - len(left.lstrip())
        right_leading_ws = len(right) - len(right.lstrip())
        left = left_leading_ws * "&nbsp;" + left
        right = +right_leading_ws * "&nbsp;" + right
        if "<span" in left or "<span" in right:
            out += f'<div style="background: {MarkupConfig.left_section_background};">{left}</div>'
            out += f'<div style="background: {MarkupConfig.right_section_background};">{right}</div>'
        else:
            out += f"<div>{left}</div>"
            out += f"<div>{right}</div>"
    return out


def html_diffs(a: str, b: str) -> str:
    """Main function to get the side-by-side diff of two strings in html."""
    a = html.escape(a)
    b = html.escape(b)

    out_a, out_b = [], []
    for sent_a, sent_b in zip(*align_seqs(sentencize(a), sentencize(b))):
        mark_a, mark_b = markup_diff(tokenize(sent_a), tokenize(sent_b), mark=mark_text)
        out_a.append(untokenize(mark_a))
        out_b.append(untokenize(mark_b))

    return html_sidebyside(out_a, out_b)
