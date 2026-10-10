"""Test Period through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import Period


def test_serializes_to_json():
    query = Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")
    expected = {
        "period": [
            {
                "period-start": "2024-01-01T00:00:00Z",
                "period-end": "2025-01-01T00:00:00Z",
            },
        ],
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<period>"
        "<period-start>2024-01-01T00:00:00Z"
        "</period-start>"
        "<period-end>2025-01-01T00:00:00Z"
        "</period-end>"
        "</period>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
