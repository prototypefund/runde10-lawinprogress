import glob
from typing import List, Tuple

import pdfplumber
import regex as re
import spacy

nlp = spacy.load("de_core_news_sm")


### Goal:
# input: raw PDF of antwurf
# output: list of (law title, change request text) pairs

## TODO:
# Spacy is messing up some of the scentences (cutting them too short)
# consider going back to manually taking first two lines unles second line start with "In" or "§"

# next wishful steps:
# Analyse entwurf patterns, common, less common etc.
# API to grab law text using that damn title
# API to grab entwurfs


def read_pdf_law(filename: str) -> str:
    """Get the raw text from the pdfs."""
    # read all pages from provided pdf
    pdf_file_obj = pdfplumber.open(filename)

    # join the pages
    return "".join(
        [page for page in [page.extract_text() for page in pdf_file_obj.pages] if page]
    )


def extract_raw_proposal(text: str) -> str:
    text = re.split("\nArtikel 1.*?\n", text, maxsplit=1)[1].split("Begründung")[0]
    return text


def extract_seperate_change_proposals(text: str) -> List[str]:
    proposals = []
    proposals.extend(re.split("Artikel\s{1,2}([1-9]|[1-9][0-9]|100)\s{0,2}\n", text))

    artikels = re.findall("Artikel\s{1,2}([1-9]|[1-9][0-9]|100)\s{0,2}\n", text)
    artikels_int = [int(artikel) for artikel in artikels]
    # compute the sum of the artikel numbers using the formula for an arithmetic series
    # using only the first and last artikel numbers, and the length of the list
    math_sum_artikels = len(artikels_int) * (artikels_int[0] + artikels_int[-1]) / 2
    # compute the sum of the artikel numbers directly
    raw_sum_artikels = sum(artikels_int)

    # uncomment next line to see if see if the next condition is met or not
    ## print(int(raw_sum_artikels), int(math_sum_artikels))

    # if the direct sum is larger than the arithmetic series, then we had an artikel from some paragraph
    # sneak into the titel list, by mentioned as "Artikel [1-100]" just before a line break :(((
    # in this case we need to go through the list and check that the artikel numbers are regularly increasing by 1
    if int(raw_sum_artikels) != int(math_sum_artikels):
        proposal_list = []
        proposal_list.append(proposals[0])
        artikel_number = 2
        for prop_index, proposal in enumerate(proposals):
            try:
                if int(proposal) == artikel_number:
                    artikel_number += artikel_number
                    proposal_list.append(proposals[prop_index + 1])
            except:
                pass
    else:
        proposal_list = proposals[
            0::2
        ]  # remove odd indexed items since they contain the artikel number only and we don't need it

    return proposal_list


def extract_law_titles(proposals_list: List[str]) -> List[str]:
    raw_titles_list = [
        list(nlp(proposal.replace("\n", " ")).sents)[0].text
        for proposal in proposals_list
    ]
    titles_clean_par_sign = [re.split("§", title)[0] for title in raw_titles_list]
    titles_clean_aenderung = []
    for title in titles_clean_par_sign:
        if re.search(r"Änderung \b(de[rs])\b ", title) is not None:
            titles_clean_aenderung.append(
                re.split(r"Änderung \b(de[rs])\b ", title)[2].strip()
            )
        else:
            titles_clean_aenderung.append(title.strip())
    return titles_clean_aenderung


def remove_inkrafttreten(titles: List[str], props: List[str]) -> Tuple[List, List]:
    if re.search("^Inkrafttreten", titles[-1]) is not None:
        titles = titles[:-1]
        props = props[:-1]

    return titles, props
