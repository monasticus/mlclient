"""Test AndNotQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import AndNotQuery, TermQuery


def test_and_not_query_serializes_to_json():
    query = AndNotQuery(TermQuery("blue"), TermQuery("green"))
    expected = {
        "and-not-query": {
            "positive-query": {"term-query": {"text": ["blue"]}},
            "negative-query": {"term-query": {"text": ["green"]}},
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_and_not_query_serializes_to_xml():
    query = AndNotQuery(TermQuery("blue"), TermQuery("green"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<and-not-query>"
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
        "</and-not-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
