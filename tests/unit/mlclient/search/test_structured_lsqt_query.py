"""Test LsqtQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import LsqtQuery


def test_serializes_to_json():
    query = LsqtQuery(
        "reports",
        timestamp="2024-01-01T00:00:00Z",
        options=["cached-incremental"],
        weight=2,
    )
    expected = {
        "lsqt-query": {
            "temporal-collection": "reports",
            "timestamp": "2024-01-01T00:00:00Z",
            "temporal-option": ["cached-incremental"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = LsqtQuery(
        "reports",
        timestamp="2024-01-01T00:00:00Z",
        options=["cached-incremental"],
        weight=2,
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<lsqt-query>"
        "<temporal-collection>reports"
        "</temporal-collection>"
        "<timestamp>2024-01-01T00:00:00Z"
        "</timestamp>"
        "<weight>2"
        "</weight>"
        "<temporal-option>cached-incremental"
        "</temporal-option>"
        "</lsqt-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
