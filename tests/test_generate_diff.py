"""Test the main script of the package."""
import importlib

import pytest
from click.testing import CliRunner

from lawinprogress.generate_diff import (
    generate_diff,
    parse_and_apply_changes,
    process_pdf,
)


# @pytest.mark.skip("PDF processing test skipped.")
@pytest.mark.parametrize(
    "pdf_path,expected",
    [
        ("./tests/data/0483-21.pdf", (["Wettbewerbsregistergesetzes"], [""])),
        (
            "./tests/data/0145-21.pdf",
            (
                [
                    "Zivilprozessordnung",
                    "Strafprozessordnung",
                    "Gesetzes über das Verfahren in Familiensachen",
                    "Elektronischer-Rechtsverkehr-Verordnung",
                    "Arbeitsgerichtsgesetzes",
                    "Arbeitsgerichtsgesetzes",
                    "Arbeitsgerichtsgesetzes zum 1. Januar  2022",
                    "Arbeitsgerichtsgesetzes zum 1. Januar",
                    "Sozialgerichtsgesetzes",
                    "Sozialgerichtsgesetzes zum 1. Januar 2022",
                    "Sozialgerichtsgesetzes zum 1. Januar 2026",
                    "Verwaltungsgerichtsordnung",
                    "Verwaltungsgerichtsordnung zum 1. Ja- nuar 2022",
                    "Verwaltungsgerichtsordnung zum 1. Ja- nuar 2026",
                    "Finanzgerichtsordnung",
                    "Finanzgerichtsordnung zum 1. Januar 2022",
                    "Finanzgerichtsordnung zum 1. Januar 2026",
                    "Bundesrechtsanwaltsordnung",
                    "Beurkundungsgesetzes",
                    "Gesetzes über die Tätigkeit europäischer Rechts- anwälte in Deutschland",
                    "Verordnung zur Einführung von Vordrucken für  das Mahnverfahren",
                    "Zustellungsvordruckverordnung",
                    "Strafvollzugsgesetzes",
                    "Grundbuchordnung",
                    "Gesetzes über die internationale Rechtshilfe in  Strafsachen",
                    "Patentanwaltsordnung",
                    "Gesetzes über Ordnungswidrigkeiten",
                    "Achten",
                ],
                [""],
            ),
        ),
        ("./tests/data/1930399.pdf", (["Strafprozessordnung"], [""])),
    ],
)
def test_process_pdf(pdf_path, expected):
    """Test if pdfs are processed as expected."""
    expected_law_titles, expected_proposals_list = expected
    law_titles, proposals_list = process_pdf(pdf_path)
    print(law_titles)

    assert len(law_titles) == len(expected_law_titles)
    assert law_titles[0] == expected_law_titles[0]
    assert len(proposals_list) == len(law_titles)
    # TODO: extend tests by expected law texts
    # assert len(proposals_list) == len(expected_proposals_list)
    # assert proposals_list[0] == expected_proposals_list[0]


def test_parse_and_apply_changes():
    """Test if changes are parsed and applied as expected."""


# @pytest.mark.skip("End2end test skipped.")
@pytest.mark.parametrize(
    "pdf_path,expected",
    [
        ("./tests/data/0483-21.pdf", "11.00/12.00 ( 91.67%)"),
        ("./tests/data/0145-21.pdf", "7.00/7.00 (100.00%)"),
        ("./tests/data/1930399.pdf", "0.00/2.00 (  0.00%)"),
    ],
)
def test_generate_diff(pdf_path, expected):
    """End-to-end test if a diff is generated.

    Mainly check if the script runs.
    """
    test_change_law_path = pdf_path  # "./tests/data/0483-21.pdf"
    test_output_path = "./tests/output/"

    runner = CliRunner()
    result = runner.invoke(
        cli=generate_diff, args=f"-c {test_change_law_path} -o {test_output_path}"
    )
    print(result.output)
    assert not result.exception
    assert result.exit_code == 0
    assert expected in result.output
    assert "DONE." in result.output
