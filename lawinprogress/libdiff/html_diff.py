"""Contains functions to generate a side-by-side diff/synopsis in html."""
import difflib
import html
from itertools import zip_longest
from typing import Callable, List, Tuple, Union

from lawinprogress.apply_changes.edit_functions import ChangeResult

from .diffhelpers import align_seqs, sentencize, tokenize, untokenize


def mark_text(tokens: List[str], kind: str) -> List[str]:
    """Put html background color on a span of text."""
    assert kind in ["add", "remove"]
    if len(tokens) > 0:
        if (tokens[0].strip()) or (len(tokens) == 1):
            tokens[0] = f'<span class="span-{kind}">{tokens[0]}'
        else:
            # in this case, the change is at the beginning of the string and we dont intend properly
            tokens[1] = f'<span class="span-{kind}">{tokens[1]}'
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
            else mark(seq_a[idx_a0:idx_a1], kind="remove")
        )
        out_b += (
            default_mark(seq_b[idx_b0:idx_b1])
            if tag == "equal"
            else mark(seq_b[idx_b0:idx_b1], kind="add")
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
    # page title
    title = left_text[0].split("source ")[-1]
    lines = []

    # show changes of the change law
    # out += "<center><h3>Änderungen</h3></center>"
    # for change_res in list(chres for res in change_results for chres in res):
    #    if change_res.status != 0:
    #        out += f'<div>&#9989; {change_res.change.raw_text}</div>'
    #    else:
    #        out += f'<div>&#274C; {change_res.change.raw_text}</div>'

    # prepare successfull changes
    success_changes = [
        [change_result for change_result in results if change_result.status != 0]
        for results in change_results
        if results
    ]

    # create the three column layout
    change_idx = 0
    for left, right in zip_longest(left_text[1:], right_text[1:], fillvalue=""):
        line = []
        left_leading_ws = len(left) - len(left.lstrip()) - 5
        right_leading_ws = len(right) - len(right.lstrip()) - 5
        left = left_leading_ws * "&nbsp;" + left.strip()
        right = right_leading_ws * "&nbsp;" + right.strip()
        # if it contains marked spans, add background color
        if "<span" in left or "<span" in right:
            # here we add background color for the left column
            line.append(f'<div class="remove-bg">{left}</div>')
            # add the changes to the change column
            try:
                line.append('<div class="change-bg" id="{}change-{}">{}</div>'.format(
                    title,
                    change_idx,
                    "<br><hr>".join(
                        [res.change.raw_text for res in success_changes[change_idx]]
                    ),
                ))
            except IndexError as err:
                # if we are out of changes expose the error
                line.append(f'<div class="change-bg" id="{title}change-{change_idx}">Something went wrong: {str(err)}</div>')
            change_idx += 1

            # here we add background color for the right column
            line.append(f'<div class="add-bg">{right}</div>')
        else:
            # if nothing to color, just put it in a plain diff
            line.append(f'<div style="padding: 2px;">{left}</div>')
            line.append('<div class="change-bg"></div>')
            line.append(f'<div style="padding: 2px;">{right}</div>')
        lines.append(line)
    return lines


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
