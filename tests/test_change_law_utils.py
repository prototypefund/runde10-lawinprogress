"""Test basic cleaning functions for change laws."""
import pytest

from lawinprogress.parsing.change_law_utils import (
    preprocess_raw_law,
    remove_footnotes,
    remove_header_footer_artifacts_from_line,
    remove_newline_in_quoted_text,
)


def test_remove_newline_in_quoted_text_simple_quotes():
    """Test if the function works properly for simple quotes."""
    test_text = "The following\n text „is \nin quotes“."

    result_text = remove_newline_in_quoted_text(test_text)

    assert result_text == "The following\n text „is  in quotes“."


def test_remove_newline_in_quoted_text_nested_quotes():
    """Test if the function works properly for nested quotes."""
    test_text = "The following\n text „is \nin „quotes\nmultiple“ times“."

    result_text = remove_newline_in_quoted_text(test_text)

    assert result_text == "The following\n text „is  in „quotes multiple“ times“."


def test_remove_newline_in_quoted_text_too_many_opening_quotes():
    """Test if the function raises an exception if the number of opening excedes the number of closing quotes."""
    test_text = (
        "The following\n text „is \nin quotes“. „This is missing closing quotes."
    )

    with pytest.raises(Exception) as err:
        result_text = remove_newline_in_quoted_text(test_text)

    assert (
        str(err.value) == "Quote error: Found more opening quotes than closing quotes."
    )


def test_remove_newline_in_quoted_text_too_many_closing_quotes():
    """Test if the function raises an exception if the number of closing excedes the number of opening quotes."""
    test_text = (
        "The following\n text „is \nin quotes“. This is missing closing quotes“."
    )

    with pytest.raises(Exception) as err:
        result_text = remove_newline_in_quoted_text(test_text)

    assert (
        str(err.value) == "Quote error: Found more closing quotes than opening quotes."
    )


def test_remove_footnotes():
    """Test if footnotes are correctly removed."""
    text_with_footnote = """genutzten  Postfach- und  Versanddienst  eines  Nutzerkontos  im  Sinne des  § 2  Absatz 5 des
Onlinezugangsgesetzes  und  der  elektronischen Poststelle des Gerichts,“.
*   Notifiziert  gemäß  der  Richtlinie  (EU)  2015/1535  des  Europäischen  Parlaments  und  des Rates vom  9.  September  2015  über  ein  Informationsver-
fahren  auf  dem Gebiet  der  technischen  Vorschriften  und  der  Vorschriften  für  die  Dienste  der  Informati-onsgesellschaft  (ABl.  L  241  vom
17.9.2015,  S.  1).  Drucksache  19/28399  – 8 –   Deutscher  Bundestag – 19. Wahlperiode
cc)  Die * bisherige Nummer 4 wird Nummer 6.
dd)  Folgender Satz wird angefügt:"""

    text_without_footnote = """genutzten  Postfach- und  Versanddienst  eines  Nutzerkontos  im  Sinne des  § 2  Absatz 5 des
Onlinezugangsgesetzes  und  der  elektronischen Poststelle des Gerichts,“.
cc)  Die * bisherige Nummer 4 wird Nummer 6.
dd)  Folgender Satz wird angefügt:"""

    print(remove_footnotes(text_with_footnote))

    assert text_without_footnote == remove_footnotes(text_with_footnote)


def test_remove_header_footer_artifacts_from_line():
    """Test if header/footer artifacts in a line of change law text can be properly removed."""
    test_line = """(2)  Eine Zustellung gegen Empfangsbekenntnis  kann auch  durch Telekopie  erfolgen.  Die  Übermittlung soll  mit dem Hinweis  „Zustellung gegen Empfangsbekenntnis“ eingeleitet werden und die absendende  Deutscher  Bundestag – 19. Wahlperiode   – 9 –   Drucksache  19/28399 Stelle, den  Namen und  die Anschrift  des  Zustellungsadressaten sowie den  Namen  des  Justizbediensteten"""
    clean_test_line = """(2)  Eine Zustellung gegen Empfangsbekenntnis  kann auch  durch Telekopie  erfolgen.  Die  Übermittlung soll  mit dem Hinweis  „Zustellung gegen Empfangsbekenntnis“ eingeleitet werden und die absendende  Stelle, den  Namen und  die Anschrift  des  Zustellungsadressaten sowie den  Namen  des  Justizbediensteten"""

    assert clean_test_line == remove_header_footer_artifacts_from_line(test_line)
