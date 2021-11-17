"""Utitlity functions to load and parse change laws."""
import regex as re


def remove_newline_in_quoted_text(text: str) -> str:
    """Remove newlines between quotation marks.

    Text in quotation marks is text that should be replaced or modified in the affected law.
    Since there can be §, sections or other bulletpoint identifiers, we remove all newlines
    in this text (so lines don't start with bullet point identifiers).

    Args:
        text: String of text to process

    Returns:
        Processed text as a string.

    Raises:
        Exception, if there are open quotes left at the end.
    """
    # find all open and closing pairs
    open_quotes = []
    quote_pairs = []
    for char_idx, char in enumerate(text):
        if char == "„":
            open_quotes.append(char_idx)
        if char == "“":
            open_quote_idx = open_quotes.pop()
            quote_pairs.append((open_quote_idx, char_idx))
            # remove the newlines between pairs of open-closing quotes
            text = (
                text[:open_quote_idx]
                + text[open_quote_idx:char_idx].replace("\n", " ")
                + text[char_idx:]
            )
    if len(open_quotes) != 0:
        # not even; raise here
        raise Exception("Something with the quotes is wrong.")
    return text


def clean_line(line: str):
    """Apply some cleaning steps to a line of change law text.strip

    Args:
        line: String of a line

    Returns:
        cleaned line
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
    return line


def remove_footnotes(text: str):
    """Remove footnotes from the full text of the change law.

    Args:
        text: Text of the law.

    Returns:
        Text without footnotes.
    """
    # try to remove footnotes
    # Inspired by the footnote on page 7 in 1928399.pdf
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
    text = text.replace("-\n", "")

    # extract the parts with change requests (here we assume only one law is affected for now)
    # > get the text between "wird wie folgt geändert" und "Begründung"
    # (allow for newlines and/or whitespace between the words)
    text = re.split(
        r"wird[\s,\n]{0,3}wie[\s,\n]{0,3}folgt[\s,\n]{0,3}geändert:", text, maxsplit=1
    )[1].split("Begründung", 1)[0]

    # remove footnotes
    text = remove_footnotes(text)

    # Remove newlines between quotation marks
    text = remove_newline_in_quoted_text(text)

    text = text.strip()  # remove trailing whitespace or newlines

    # pull every bulletpoint content to one line
    outtext = ""
    for line in text.split("\n"):
        # apply some cleaning
        line = clean_line(line)

        # check if line starts with a bullet point identifier
        # > if yes, put it in a new line, otherwise just append the linetext to the text
        if any(
            [
                re.match(r"^\d{1,2}\.", line),
                re.match(r"^[a-z]\)", line),
                re.match(r"^[a-z][a-z]\)", line),
                re.match(r"^\([a-z0-9]\)", line),
            ]
        ):
            outtext += "\n" + line
        else:
            outtext += line

    return outtext.strip()
