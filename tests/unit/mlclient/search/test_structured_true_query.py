"""Test TrueQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import TrueQuery


def test_true_query_serializes_to_json():
    query = TrueQuery()
    expected = {"true-query": None}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_true_query_serializes_to_xml():
    query = TrueQuery()
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<true-query />"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
