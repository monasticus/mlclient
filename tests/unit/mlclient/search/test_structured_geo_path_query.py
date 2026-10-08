"""Test GeoPathQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import GeoPathQuery, PathIndex, Point


def test_serializes_to_json():
    query = GeoPathQuery(
        PathIndex("/place/location"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = {
        "geo-path-query": {
            "path-index": {"text": "/place/location"},
            "fragment-scope": "properties",
            "geo-option": ["units=miles"],
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoPathQuery(
        PathIndex("/place/location"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geo-path-query>"
        "<path-index>/place/location"
        "</path-index>"
        "<geo-option>units=miles"
        "</geo-option>"
        "<fragment-scope>properties"
        "</fragment-scope>"
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>20"
        "</longitude>"
        "</point>"
        "<weight>2"
        "</weight>"
        "</geo-path-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
