"""Test basic cleaning functions for change laws."""
import pytest

from lawinprogress.parsing.change_law_utils import remove_newline_in_quoted_text, preprocess_raw_law


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


def test_remove_newline_in_quoted_text_uneven_numbered_quotes():
    """Test if the function raises an exception if the number of opening and closing quotes is not equal."""
    test_text = "The following\n text „is \nin quotes“. „This is missing closing quotes."

    with pytest.raises(Exception) as err:
        result_text = remove_newline_in_quoted_text(test_text)

    assert str(err.value) == "Something with the quotes is wrong."
