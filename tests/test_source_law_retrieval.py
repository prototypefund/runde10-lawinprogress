""" test the functions for getting and handling source laws """
import pytest
import requests

from lawinprogress.processing.source_law_retrieval import (
    FuzzyLawSlugRetriever,
    get_source_law_rechtsinformationsportal,
)


class MockResponse:

    # mock status_code property always returns 200
    @property
    def status_code(self):
        return 200

    # mock json() method always returns a specific testing dictionary
    @staticmethod
    def json():
        return_keys = {
            "type",
            "id",
            "name",
            "title",
            "parent",
            "body",
            "footnotes",
        }
        return {
            "data": {
                "contents": [
                    {key: "test_value" for key in return_keys} for _ in range(5)
                ]
            }
        }


def test_get_source_law_rechtsinformationsportal_success(monkeypatch):
    """Test if the API request for a source law was successful."""
    return_keys = {
        "type",
        "id",
        "name",
        "title",
        "parent",
        "body",
        "footnotes",
    }

    def mock_get(*args, **kwargs):
        return MockResponse()

    # apply the monkeypatch for requests.get to mock_get
    monkeypatch.setattr(requests, "get", mock_get)

    # call the function
    source_law = get_source_law_rechtsinformationsportal(slug="test")

    assert len(source_law) == 5
    assert set(source_law[0].keys()) == return_keys


@pytest.mark.parametrize(
    "test_law_title,expected_slug",
    [
        ("Wettbewerbsregistergesetzes", "wregg"),
        ("Zivilprozessordnung", "zpo"),
        ("Strafprozessordnung", "stpo"),
        ("Arbeitsgerichtsgesetzes zum 1. Januar 2022", "arbgg"),
    ],
)
def test_fuzzy_slug_retrieval(test_law_title, expected_slug):
    """Test if slug retieval works and fails as expected."""
    slug = FuzzyLawSlugRetriever.fuzzyfind(test_law_title)
    assert slug == expected_slug
