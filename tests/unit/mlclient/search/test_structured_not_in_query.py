"""Test NotInQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import NotInQuery, TermQuery


def test_not_in_query_serializes_to_json():
    query = NotInQuery(TermQuery("blue"), TermQuery("green"))
    expected = {
        "not-in-query": {
            "positive-query": {"term-query": {"text": ["blue"]}},
            "negative-query": {"term-query": {"text": ["green"]}},
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_not_in_query_serializes_to_xml():
    query = NotInQuery(TermQuery("blue"), TermQuery("green"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<not-in-query>"
        "<positive-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</positive-query>"
        "<negative-query>"
        "<term-query>"
        "<text>green</text>"
        "</term-query>"
        "</negative-query>"
        "</not-in-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
