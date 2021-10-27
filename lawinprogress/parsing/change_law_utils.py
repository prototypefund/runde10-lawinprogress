"""Utitlity functions to load and parse change laws."""
import regex as re


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

    # remove newlines between quotation marks
    # > text in quotation marks is text that should be replaced or modified in the affected law.
    # > Since there can be §, sections or other bulletpoint identifiers,
    # > we remove all newlines in this text (so lines don't start with bullet point identifiers)
    for match in re.finditer(r"(?<=„)(.|\n)*?(?=“)", text, re.MULTILINE):
        text = (
            text[: match.span()[0]]
            + text[match.span()[0] : match.span()[1]].replace("\n", " ")
            + text[match.span()[1] :]
        )

    # remove text artifacts from the page
    text = re.sub(r"\.?Drucksache \d{2,3}\/\d{1,2}", "", text)  # Drucksache...
    text = re.sub(r"- \d -", "", text)  # page numbering
    text = text.strip()  # remove trailing whitespace or newlines

    # pull every bulletpoint content to one line
    outtext = ""
    for line in text.split("\n"):
        line = line.strip()
        # if a line starts with a single digit, we suppose its a page number and remove it
        line = re.sub(r"^\d{1,2}\s", "", line)
        if any(string in line for string in ["*", "Drucksache"]):
            line = ""
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
