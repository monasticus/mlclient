"""Test OrQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import OrQuery, TermQuery


def test_or_query_serializes_to_json():
    query = OrQuery([TermQuery("blue"), TermQuery("green")])
    expected = {
        "or-query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"term-query": {"text": ["green"]}},
            ],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_or_query_serializes_to_xml():
    query = OrQuery([TermQuery("blue"), TermQuery("green")])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<or-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "<term-query>"
        "<text>green</text>"
        "</term-query>"
        "</or-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_or_query_empty():
    query = OrQuery(())
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<or-query />"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
