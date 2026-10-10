"""Test operator-state serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import OperatorState


def test_serializes_to_json():
    query = OperatorState("sort", "relevance")
    expected = {
        "operator-state": [{"operator-name": "sort", "state-name": "relevance"}],
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = OperatorState("sort", "relevance")
    expected = ElementTree.fromstring(
        '<operator-state xmlns="http://marklogic.com/appservices/search">'
        "<operator-name>sort</operator-name><state-name>relevance</state-name>"
        "</operator-state>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
