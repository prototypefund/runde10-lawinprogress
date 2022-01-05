"""Contains helper functions for diffing."""
import difflib
from typing import List, Tuple


def tokenize(string: str) -> List[str]:
    """Split a string into tokens by whitespace."""
    leading_ws = len(string) - len(string.lstrip())
    return [leading_ws * " "] + string.split()


def untokenize(tokens: List[str]) -> str:
    """Join a list of tokens into a string"""
    return " ".join(tokens)


def sentencize(string: str) -> List[str]:
    """Split a string into a list of texts by splitting on newline."""
    return string.split("\n")


def align_seqs(
    seq_a: List[str], seq_b: List[str], fill: str = ""
) -> Tuple[List[str], List[str]]:
    out_a, out_b = [], []
    seqmatcher = difflib.SequenceMatcher(a=seq_a, b=seq_b, autojunk=False)
    for _, idx_a0, idx_a1, idx_b0, idx_b1 in seqmatcher.get_opcodes():
        delta = (idx_a1 - idx_a0) - (idx_b1 - idx_b0)
        out_a += seq_a[idx_a0:idx_a1] + [fill] * max(-delta, 0)
        out_b += seq_b[idx_b0:idx_b1] + [fill] * max(delta, 0)
    assert len(out_a) == len(out_b)
    return out_a, out_b
