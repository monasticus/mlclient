"""Test AndQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import AndQuery, TermQuery


def test_and_query_serializes_to_json():
    query = AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True)
    expected = {
        "and-query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"term-query": {"text": ["green"]}},
                {"ordered": {"_value": True}},
            ],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_and_query_serializes_to_xml():
    query = AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True)
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<and-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "<term-query>"
        "<text>green</text>"
        "</term-query>"
        "<ordered>true</ordered>"
        "</and-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_and_query_empty():
    query = AndQuery([])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<and-query />"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
