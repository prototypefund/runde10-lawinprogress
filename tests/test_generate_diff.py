"""Test the main script of the package."""
import pytest
from click.testing import CliRunner

from lawinprogress.generate_diff import generate_diff


# @pytest.mark.skip("End2end test skipped.")
def test_generate_diff():
    """Test of a diff is generated.

    Mainly check if the script runs.
    """
    test_change_law_path = "./tests/data/0483-21.pdf"
    test_output_path = "./tests/output/"

    runner = CliRunner()
    result = runner.invoke(
        cli=generate_diff, args=f"-c {test_change_law_path} -o {test_output_path}"
    )
    print(result.output)
    assert not result.exception
    assert result.exit_code == 0
    assert "11/12 ( 91.67%)" in result.output
    assert "DONE." in result.output
