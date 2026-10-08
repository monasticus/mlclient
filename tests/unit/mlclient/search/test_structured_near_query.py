"""Test NearQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import NearQuery, TermQuery


def test_near_query_serializes_to_json():
    query = NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
    expected = {
        "near-query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"term-query": {"text": ["green"]}},
                {"distance": {"_value": 3}},
                {"minimum-distance": {"_value": 1}},
                {"distance-weight": {"_value": 2}},
                {"ordered": {"_value": False}},
            ],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_near_query_serializes_to_xml():
    query = NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<near-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "<term-query>"
        "<text>green</text>"
        "</term-query>"
        "<distance>3</distance>"
        "<minimum-distance>1</minimum-distance>"
        "<distance-weight>2</distance-weight>"
        "<ordered>false</ordered>"
        "</near-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_near_query_with_zero():
    query = NearQuery(TermQuery("blue"), distance=0, distance_weight=0)
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<near-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "<distance>0</distance>"
        "<distance-weight>0</distance-weight>"
        "</near-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
