"""Test the processing of change law pdfs."""
import pytest

from lawinprogress.processing.proposal_pdf_to_artikles import process_pdf


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
    law_titles, proposals_list, full_law_title = process_pdf(pdf_path)
    print(law_titles)

    assert len(law_titles) == len(expected_law_titles)
    assert law_titles[0] == expected_law_titles[0]
    assert len(proposals_list) == len(law_titles)
    # TODO: extend tests by expected law texts
    # assert len(proposals_list) == len(expected_proposals_list)
    # assert proposals_list[0] == expected_proposals_list[0]
