""" test the functions for getting and handling source laws """
import pytest
import requests

from lawinprogress.source_law_api import get_source_law_rechtsinformationsportal


class MockResponse:

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
