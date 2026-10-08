"""Test FalseQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import FalseQuery


def test_false_query_serializes_to_json():
    query = FalseQuery()
    expected = {"false-query": None}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_false_query_serializes_to_xml():
    query = FalseQuery()
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<false-query />"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
