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
    title: str,
) -> str:
    """Create a side-by-side div-table for the diff/synopsis."""
    # page title
    out = f'<center><h2 id="{title}law-title">{title}</h2></center>'

    # prepare successfull changes
    success_changes = [
        [change_result for change_result in results if change_result.status != 0]
        for results in change_results
        if results
    ]

    # create the three column layout
    change_idx = 0  # count the changes for indexing html ids
    old, change, new = [], [], []
    for left, right in zip_longest(left_text[1:], right_text[1:], fillvalue=""):
        left_leading_ws = len(left) - len(left.lstrip()) - 5
        right_leading_ws = len(right) - len(right.lstrip()) - 5
        # style the headlines a bit
        if left_leading_ws == 0:
            left = '<h3 class="title is-4">' + left.strip() + "</h3>"
            right = '<h3 class="title is-4">' + right.strip() + "</h3>"
        elif left_leading_ws == 4:
            left = '<h3 class="title is-5">' + 4*"&nbsp;" + left.strip() + "</h3>"
            right = '<h3 class="title is-5">' + 4*"&nbsp;" + right.strip() + "</h3>"
        else:
            left = left_leading_ws * "&nbsp;" + left.strip()
            right = right_leading_ws * "&nbsp;" + right.strip()
        # if it contains marked spans, add background color
        if "<span" in left or "<span" in right:
            # here we add background color for the left column
            old.append(f'<div class="remove-bg old" id="{title}old-{change_idx}">{left}</div>')
            # add the changes to the change column
            try:
                change.append('<div class="change-bg change" id="{}change-{}">{}</div>'.format(
                    title,
                    change_idx,
                    "<br><hr>".join(
                        [res.change.raw_text for res in success_changes[change_idx]]
                    ),
                ))
            except IndexError as err:
                # if we are out of changes expose the error
                change.append(f'<div class="change-bg change" id="{title}change-{change_idx}">Something went wrong: {str(err)}</div>')
            # here we add background color for the right column
            new.append(f'<div class="add-bg new" id="{title}new-{change_idx}">{right}</div>')

            change_idx += 1
        else:
            # if nothing to color, just put it in a plain diff
            old.append(f'<div style="padding: 2px;" class="old">{left}</div>')
            change.append('<div class="change-bg change"></div>')
            new.append(f'<div style="padding: 2px;" class="new">{right}</div>')

    # return lines
    return [(old_i, change_i, new_i) for old_i, change_i, new_i in zip(old, change, new)]


def html_diffs(
    text_a: str, text_b: str, change_results: List[List[ChangeResult]], title: str
) -> str:
    """Main function to get the side-by-side diff of two strings in html."""
    text_a = html.escape(text_a)
    text_b = html.escape(text_b)

    out_a, out_b = [], []
    for sent_a, sent_b in zip(*align_seqs(sentencize(text_a), sentencize(text_b))):
        mark_a, mark_b = markup_diff(tokenize(sent_a), tokenize(sent_b), mark=mark_text)
        out_a.append(untokenize(mark_a))
        out_b.append(untokenize(mark_b))

    return html_sidebyside(out_a, out_b, change_results, title)
