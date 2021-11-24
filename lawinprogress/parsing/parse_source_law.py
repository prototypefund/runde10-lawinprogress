"""Functions and classes to parse the source law into a tree."""
import regex as re

from lawinprogress.parsing.lawtree import LawTextNode


def parse_source_law_tree(text: str, source_node: LawTextNode) -> LawTextNode:
    """Parse raw law text into a structured format.

    Look for bullet point patters and build a tree with it.

    Args:
        text: raw text of the law.

    Returns:
        Structured output. A tree of LawTextNodes.
    """
    patterns = [
        r"\n§\s*\d{1,3}[a-z]?",
        r"\n\s*\([a-z1-9]\)",
        r"\n\s*\d{1,2}\.",
        r"\n\s*[a-z]\)",
    ]

    # build the tree
    for pattern in patterns:
        used_texts = []
        # search the pattern in the text
        if re.search(pattern, text):
            split_text = re.split(pattern, text)
            for idx, match in enumerate(re.finditer(pattern, text)):
                new_node = LawTextNode(
                    text=re.split("|".join(patterns), split_text[idx + 1].strip())[0],
                    # store the text for this bullet point on this level
                    bulletpoint=text[match.span()[0] : match.span()[1]].strip(),
                    # apply the function recursively to get all levels
                    parent=source_node,
                )
                # get the next level associated with this node
                _ = parse_source_law_tree(split_text[idx + 1], source_node=new_node)
                # store the text already used to remove later. Store bulletpoint and text
                used_texts.append(text[match.span()[0] : match.span()[1]] + split_text[idx + 1])
        # if parsing has happened for a piece of text, we remove it.
        for used_text in used_texts:
            text = text.replace(used_text, "")
    return source_node
