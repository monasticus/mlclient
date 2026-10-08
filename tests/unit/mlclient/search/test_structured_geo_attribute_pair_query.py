"""Test GeoAttributePairQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import Attribute, Element, GeoAttributePairQuery, Point


def test_serializes_to_json():
    query = GeoAttributePairQuery(
        Element("place"),
        Attribute("lat"),
        Attribute("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = {
        "geo-attr-pair-query": {
            "parent": {"name": "place", "ns": ""},
            "lat": {"name": "lat", "ns": ""},
            "lon": {"name": "lon", "ns": ""},
            "fragment-scope": "properties",
            "geo-option": ["units=miles"],
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoAttributePairQuery(
        Element("place"),
        Attribute("lat"),
        Attribute("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geo-attr-pair-query>"
        '<parent name="place" ns=""/>'
        '<lat name="lat" ns=""/>'
        '<lon name="lon" ns=""/>'
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
        "</geo-attr-pair-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
