"""Functions to process a raw pdf and extract clean titles and proposals."""
from typing import List, Tuple

import pdfplumber
import regex as re


def read_pdf_law(filename: str) -> str:
    """Get the raw text from the pdfs."""
    # read all pages from provided pdf
    pdf_file_obj = pdfplumber.open(filename)

    # join the pages
    return "\n".join(
        [page for page in [page.extract_text() for page in pdf_file_obj.pages] if page]
    )


def extract_raw_proposal(text: str) -> str:
    """Extract the part of the pdf where the proposals are.

    Between Artikel 1 and Begründung.

    Args:
        text: Text of the full pdf.

    Returns:
        Proposal text.
    """
    # extract the full title of the law
    full_law_title = re.search(r"\nEntwurf(.|\n)*?A.", text)[0].split("(")[0]
    return re.split(r"\nArtikel 1.*?\n", text, maxsplit=1)[1].split("Begründung")[0], full_law_title


def extract_separate_change_proposals(text: str) -> List[str]:
    """Function to extract the texts of the different propsals for different affected laws.

    Args:
        text: Full text of the change law.

    Returns:
        List of parts of the change law affecting differnt laws.
    """
    proposals = []
    proposals.extend(re.split(r"\nArtikel\s{1,2}([0-9]{1,3})\s{0,2}\n", text))

    artikels = re.findall(r"\nArtikel\s{1,2}([1-9]|[1-9][0-9]|100)\s{0,2}\n", text)
    artikels_int = [int(artikel) for artikel in artikels]
    # compute the sum of the artikel numbers using the formula for an arithmetic series
    # using only the first and last artikel numbers, and the length of the list
    math_sum_artikels = len(artikels_int) * (artikels_int[0] + artikels_int[-1]) / 2
    # compute the sum of the artikel numbers directly
    raw_sum_artikels = sum(artikels_int)

    # uncomment next line to see if the next condition is met or not
    # print(int(raw_sum_artikels), int(math_sum_artikels))

    # if the direct sum is larger than the arithmetic series,
    # then we had an artikel from some paragraphs
    # sneak into the titel list, by mentioned as "Artikel [1-100]" just before a line break :(((
    # in this case we need to go through the list and check that
    # the artikel numbers are regularly increasing by 1
    if int(raw_sum_artikels) != int(math_sum_artikels):
        proposal_list = [proposals[0]]
        artikel_number = 2
        for prop_index, proposal in enumerate(proposals):
            try:
                if int(proposal) == artikel_number:
                    artikel_number += artikel_number
                    proposal_list.append(proposals[prop_index + 1])
            except:
                pass
    else:
        # remove odd indexed items since they contain the artikel number only, and we don't need it
        proposal_list = proposals[0::2]

    return proposal_list


def extract_law_titles(proposals_list: List[str]) -> List[str]:
    """Extract the title of the law affected by the proposal.replace

    Args:
        proposals_list: List of proposal texts.
    """
    raw_titles_list = []
    for proposal in proposals_list:
        raw_title = ""
        proposal_lines = ("#" + proposal.lstrip()).split("\n")
        last_line_is_title = False
        for line in proposal_lines:
            # add lines starting with Änderung or similar
            if any(re.match(pattern, line)
                for pattern in [
                    "^#Änderung",
                    "^#Weitere\s*Änderung",
                    "^#Folgeänderungen",
                ]
            ):
                raw_title += line
                last_line_is_title = True
                continue
            # if the following line starts with lowercase letter or number also add it
            if last_line_is_title and (line[0].islower() or line[0].isnumeric()):
                raw_title += " " + line
                continue
            # if nothing more to add, append and move on
            if last_line_is_title:
                last_line_is_title = False
                raw_titles_list.append(raw_title.replace("- ", ""))

    titles_clean_par_sign = [re.split(r"§", title)[0] for title in raw_titles_list]
    titles_clean_aenderung = []
    for title in titles_clean_par_sign:
        if re.search(r"Änderung \b(de[rs])\b ", title) is not None:
            clean_title = re.split(r"Änderung \b(de[rs])\b ", title)[2].strip()
            titles_clean_aenderung.append(clean_title)
        else:
            titles_clean_aenderung.append(title.strip().lstrip("#"))
    return titles_clean_aenderung


def remove_inkrafttreten(titles: List[str], props: List[str]) -> Tuple[List, List]:
    """Remove the last artikel of a change law, namely 'Inkrafttreten'."""
    if re.search(r"^Inkrafttreten", props[-1]) is not None:
        props = props[:-1]

    return titles, props
