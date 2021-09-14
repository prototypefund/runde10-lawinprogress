"""Functions and classes to parse the source law into a tree."""
import regex as re
from anytree import NodeMixin, RenderTree, findall


class LawTextNode(NodeMixin):
    def __init__(self, text, bulletpoint, parent=None, children=None):
        self.text = text
        self.bulletpoint = bulletpoint
        self.parent = parent
        if children:  # set children only if given
             self.children = children
                
    def __repr__(self):
        return "{} - {}".format(self.bulletpoint, self.text)
    
    def _to_text(self):
        """return the full law text"""
        treestr = ""
        for pre, fill, node in RenderTree(self):
            treestr += "{}{} {}\n".format(" "*len(pre),node.bulletpoint, node.text)
        return treestr
    
    def _print(self):
        for pre, fill, node in RenderTree(self):
            treestr = u"{}{} - {}".format(pre, node.bulletpoint, node.text)
            print(treestr.ljust(8))


def parse_source_law_tree(text: str, source_node = LawTextNode(text="source", bulletpoint="source")) -> LawTextNode:
    """Parse raw law text into a structured format.
    
    Look for bullet point patters and build a tree with it.
    
    Args:
        text: raw text of the law.
        
    Returns:
        Structured output. A tree of LawTextNodes.
    """
    patterns = [r"\n§\s\d{1,3}[a-z]?", r"\n\s*\([a-z1-9]\)", r"\n\s*\d{1,2}\.", r"\n\s*[a-z]\)"]
    
    # build the tree
    for pattern in patterns:
        used_texts = []
        # search the pattern in the text
        if re.search(pattern, text):
            split_text = re.split(pattern, text)
            for idx, m in enumerate(re.finditer(pattern, text)):
                new_node = LawTextNode(
                    text=split_text[idx + 1].strip().split("\n")[0],
                    # store the text for this bullet point on this level
                    bulletpoint=text[m.span()[0]: m.span()[1]].strip(),
                    # apply the function recursively to get all levels
                    parent=source_node
                )
                # get the next level associated with this node
                _ = parse_source_law_tree(split_text[idx + 1], source_node=new_node)
                used_texts.append(split_text[idx + 1])
        for ut in used_texts:
            text = text.replace(ut, "")
    return source_node