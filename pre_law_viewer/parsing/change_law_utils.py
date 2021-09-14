"""Utitlity functions to load and parse change laws."""
import pdfplumber
import regex as re
from typing import List, Tuple
import spacy


nlp = spacy.load("de_core_news_sm")


def read_pdf_law(filename: str) -> str:
    """Get the raw text from the pdfs."""
    # read all pages from provided pdf
    pdf_file_obj = pdfplumber.open(filename)

    # join the pages and remove bindestrich newline gaps
    return "".join([page for page in [page.extract_text() for page in pdf_file_obj.pages] if page]).replace("-\n", "")


def extract_raw_proposal(text: str) -> str:
    text = re.split('\nArtikel 1.*?\n', text, maxsplit=1)[1].split('Begründung')[0]
    return text


def extract_seperate_change_proposals(text: str) -> List[str]:
    proposals = []
    proposals.extend(re.split('Artikel\s{1,2}([1-9]|[1-9][0-9]|100)\s{0,2}\n',text))
    
    artikels = re.findall('Artikel\s{1,2}([1-9]|[1-9][0-9]|100)\s{0,2}\n',text)
    artikels_int = [int(artikel) for artikel in artikels]
    # compute the sum of the artikel numbers using the formula for an arithmetic series
    # using only the first and last artikel numbers, and the length of the list
    math_sum_artikels = len(artikels_int)*(artikels_int[0]+artikels_int[-1])/2
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
                    proposal_list.append(proposals[prop_index+1])
            except:
                pass
    else:
        proposal_list = proposals[0::2] # remove odd indexed items since they contain the artikel number only and we don't need it

    return proposal_list


def extract_law_titles(proposals_list: List[str]) -> List[str]:
    raw_titles_list = [list(nlp(proposal.replace('\n',' ')).sents)[0].text for proposal in proposals_list]
    titles_clean_par_sign = [re.split('§',title)[0] for title in raw_titles_list]
    titles_clean_aenderung = []
    for title in titles_clean_par_sign:
        if re.search(r'Änderung \b(de[rs])\b ',title) is not None:
            titles_clean_aenderung.append(re.split(r'Änderung \b(de[rs])\b ',title)[2].strip())
        else:
            titles_clean_aenderung.append(title.strip())
    return titles_clean_aenderung


def remove_inkrafttreten(titles: List[str], props: List[str]) -> Tuple[List,List]:
    if re.search('^Inkrafttreten', titles[-1]) is not None:
        titles = titles[:-1]
        props = props[:-1]
    return titles, props


def preprocess_raw_law(text: str) -> str:
    """Apply some preprocessing to the raw text of the laws.
    
    Every line in the output starts with a "bullet point identifier" (e.g. § 2, (1), b), aa))
    
    Args:
        text: string containing the law text.
    
    Returns:
        String with preprocessing applied.
    """
    # extract the parts with change requests (here we assume only one law is affected for now)
    #> get the text between "wird wie folgt geändert" und "Begründung" (allow for newlines and/or whitespace between the words)
    text = re.split(r"wird[\s,\n]{0,3}wie[\s,\n]{0,3}folgt[\s,\n]{0,3}geändert:", text, maxsplit=1)[1].split("Begründung", 1)[0]

    # remove newlines between quotation marks
    #> text in quotation marks is text that should be replaced or modified in the affected law.
    #> Since there can be §, sections or other bulletpoint identifiers,
    #> we remove all newlines in this text (so lines don't start with bullet point identifiers)
    for m in re.finditer(r"(?<=„)(.|\n)*?(?=“)", text, re.MULTILINE):
        text = text[:m.span()[0]] + text[m.span()[0]:m.span()[1]].replace("\n", " ") + text[m.span()[1]:]  #).replace("  ", " ")

    # remove text artifacts from the page
    text = re.sub(r"\.?Drucksache \d{2,3}\/\d{1,2}", "", text)  # Drucksache...
    text = re.sub(r"- \d -", "", text)  # page numbering
    text = text.strip()  # remove trailing whitespace or newlines
    
    # pull every bulletpoint content to one line
    outtext = ""
    for line_num, line in enumerate(text.split("\n")):
        # check if line starts with a bullet point identifier
        #> if yes, put it in a new line, otherwise just append the linetext to the text
        if any([
            re.match(r"^\d\.", line),
            re.match(r"^[a-z]\)", line),
            re.match(r"^[a-z][a-z]\)", line),
            re.match(r"^\([a-z1-9]\)", line)
        ]):
            outtext += "\n" + line
        else:
            outtext += line
            
    return outtext.strip()


def expand_text(text: str) -> str:
    """Expand the lines, such that every line is one complete change request.
    
    Args:
        text: preprocessed text.
        
    Returns:
        Expanded text. Every line contains one change request text.
    """
    outtext = ""
    stack = []
    for line in text.split("\n"):
        if re.match(r"^\d\.", line):
            if stack:
                outtext += " ".join(stack) + "\n"
            stack = []
            stack.append(line)
        if re.match(r"^[a-z]\)", line):
            if len(stack) >= 2:
                outtext += " ".join(stack) + "\n"
                stack.pop()
            stack.append(line)
        if re.match(r"^[a-z][a-z]\)", line):
            if len(stack) >= 3:
                outtext += " ".join(stack) + "\n"
                stack.pop()
            stack.append(line)
    if stack:
        outtext += " ".join(stack) + "\n"
    return outtext.strip()