"""Test NotQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import NotQuery, TermQuery


def test_not_query_serializes_to_json():
    query = NotQuery(TermQuery("blue"))
    expected = {"not-query": {"term-query": {"text": ["blue"]}}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_not_query_serializes_to_xml():
    query = NotQuery(TermQuery("blue"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<not-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</not-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
