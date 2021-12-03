"""Contains helper functions for diffing."""
import difflib
from typing import List, Tuple


def tokenize(string: str) -> List[str]:
    """Split a string into tokens by whitespace."""
    # outlist = []
    # for token in nlp(string):
    #    outlist.extend([token.text, token.whitespace_])
    # return outlist
    leading_ws = len(string) - len(string.lstrip())
    return [leading_ws * " "] + string.split()


def untokenize(tokens: List[str]) -> str:
    """Join a list of tokens into a string"""
    return " ".join(tokens)


def sentencize(string: str) -> List[str]:
    """Split a string into a list of texts by splitting on newline."""
    return string.split("\n")


def unsentencise(strings: List[str]) -> str:
    """Join a list of texts into a string."""
    return "".join(strings)


def align_seqs(
    a: List[str], b: List[str], fill: str = ""
) -> Tuple[List[str], List[str]]:
    out_a, out_b = [], []
    seqmatcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        delta = (a1 - a0) - (b1 - b0)
        out_a += a[a0:a1] + [fill] * max(-delta, 0)
        out_b += b[b0:b1] + [fill] * max(delta, 0)
    assert len(out_a) == len(out_b)
    return out_a, out_b
