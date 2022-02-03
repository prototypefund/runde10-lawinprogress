"""Utitlity functions to load and parse change laws."""
import logging

import regex as re


class QuotationMismatchError(Exception):
    """Exception raised for mismatch in opening and closing quotes.append

    Attributes:
        message: String with an error message.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


def remove_newline_in_quoted_text(text: str, fix: bool = False) -> str:
    """Remove newlines between quotation marks.

    Text in quotation marks is text that should be replaced or modified in the affected law.
    Since there can be §, sections or other bulletpoint identifiers, we remove all newlines
    in this text (so lines don't start with bullet point identifiers).

    Args:
        text: String of text to process
        fix: If a crude way of fixing should be applied. No exceptions will be raised then.

    Returns:
        Processed text as a string.

    Raises:
        QuotationMismatchError, if there is an unequal number of opening and closing quotes.
    """
    # find all open and closing pairs
    open_quotes = []
    quote_pairs = []
    for char_idx, char in enumerate(text):
        if char == "„":
            open_quotes.append(char_idx)
        if char == "“":
            try:
                open_quote_idx = open_quotes.pop()
            except IndexError as err:
                # more closing quotes than opening quotes.
                raise QuotationMismatchError(
                    "Number of opening quotes < number of closing quotes."
                )

            quote_pairs.append((open_quote_idx, char_idx))
            # remove the newlines between pairs of open-closing quotes
            text = (
                text[:open_quote_idx]
                + text[open_quote_idx:char_idx].replace("\n", " ")
                + text[char_idx:]
            )
    if len(open_quotes) != 0:
        if fix:
            text = remove_newline_in_quoted_text(text + "“" * len(open_quotes))
        else:
            # more open quotes than closing quotes.
            raise QuotationMismatchError(
                "Number of opening quotes > number of closing quotes."
            )
    return text


def remove_header_footer_artifacts_from_line(line: str):
    """Apply cleaning steps to remove artifacts from page headers and footers.

    Example artifacts are Drucksache and Pagenumbering.

    Args:
        line: String of a line

    Returns:
        String of the line with the artifacts removed.
    """
    line = line.strip()

    # if a line starts with a single digit, we suppose its a page number and remove it
    line = re.sub(r"^\d{1,2}\s", "", line)
    # line = re.sub(r"- \d -", "", line)

    #  remove drucksache page break stuff
    drucksache_regexs = [
        r"\sDeutscher\s{1,5}Bundestag\s{1,5}\S\s{1,5}\d{1,2}\.\s{1,3}Wahlperiode\s{1,5}\S\s{1,5}\d{1,3}\s{1,5}\S\s{1,5}Drucksache\s{1,5}\d{1,3}\/\d{1,7}",
        r"\sDrucksache\s{1,5}\d{1,3}\/\d{1,7}\s{1,5}\S\s{1,5}\d{1,2}\s{1,5}\S\s{1,5}Deutscher\s{1,3}Bundestag\s{1,5}\S\s{1,5}\d{1,2}\.\s{1,3}Wahlperiode\s",
    ]
    for drucksache_regex in drucksache_regexs:
        line = re.sub(drucksache_regex, "", line)
    if "drucksache" in line.lower():
        return "\n"
    return line


def remove_footnotes(text: str):
    """Remove footnotes from the full text of the change law.

    Currently this is only a simple approach that worked in one case
    removing the text between * and Wahlperiode.

    Args:
        text: Text of the law.

    Returns:
        Text without footnotes.
    """
    # try to remove footnotes
    # remove the text between * and Wahlperiode\s
    # Inspired by the footnote on page 7 in 1928399.pdf where it works.
    return re.sub(r"\*(.|\n)*?Wahlperiode\s", "", text)


def preprocess_raw_law(text: str) -> str:
    """Apply some preprocessing to the raw text of the laws.

    Every line in the output starts with a "bullet point identifier" (e.g. § 2, (1), b), aa))

    Args:
        text: string containing the law text.

    Returns:
        String with preprocessing applied.
    """
    # remove linebreak wordsplits
    text = re.sub(r"\b-\n\b", "", text)

    # remove header and footer artifacts
    text = "\n".join(
        [remove_header_footer_artifacts_from_line(line) for line in text.split("\n")]
    )

    # remove footnotes
    text = remove_footnotes(text)

    # Remove newlines between quotation marks
    try:
        text = remove_newline_in_quoted_text(text)
    except QuotationMismatchError as err:
        logging.warning(err)
        text = remove_newline_in_quoted_text(text, fix=True)

    text = text.strip()  # remove trailing whitespace or newlines

    # pull every bulletpoint content to one line
    outtext = ""
    for line in text.split("\n"):
        # check if line starts with a bullet point identifier
        # > if yes, put it in a new line, otherwise just append the linetext to the text
        if any(
            [
                re.match(r"^\d{1,2}\.", line),
                re.match(r"^[a-z]\)", line),
                re.match(r"^[a-z][a-z]\)", line),
                re.match(r"^\([a-z0-9]{1,3}\)", line),
            ]
        ):
            outtext += "\n" + line
        elif any(re.match(pattern, line) for pattern in [r"^§", r"^(In|Dem|Nach)\s*§"]):
            outtext += "\n## " + line
        else:
            outtext += line

    return outtext.strip()
