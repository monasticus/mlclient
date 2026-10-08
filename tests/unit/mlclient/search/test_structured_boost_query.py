"""Test BoostQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import BoostQuery, TermQuery


def test_boost_query_serializes_to_json():
    query = BoostQuery(TermQuery("blue"), TermQuery("green", weight=2))
    expected = {
        "boost-query": {
            "matching-query": {"term-query": {"text": ["blue"]}},
            "boosting-query": {"term-query": {"text": ["green"], "weight": 2}},
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_boost_query_serializes_to_xml():
    query = BoostQuery(TermQuery("blue"), TermQuery("green", weight=2))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<boost-query>"
        "<matching-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</matching-query>"
        "<boosting-query>"
        "<term-query>"
        "<text>green</text>"
        "<weight>2</weight>"
        "</term-query>"
        "</boosting-query>"
        "</boost-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
