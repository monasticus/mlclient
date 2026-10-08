"""Test GeoElementQuery through its public API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import Element, GeoElementQuery, Point


def test_geo_element_query_without_parent():
    query = GeoElementQuery(Element("location"), Point(10, 20))
    assert query.serialize() == {
        "geo-elem-query": {
            "element": {"name": "location", "ns": ""},
            "point": [{"latitude": 10, "longitude": 20}],
        },
    }


def test_geo_element_query_rejects_nonregion():
    with pytest.raises(TypeError) as exc:
        GeoElementQuery(Element("location"), "10,20")
    assert str(exc.value) == "Geospatial criteria must be Region instances."


def test_serializes_to_json():
    query = GeoElementQuery(
        Element("location"),
        Point(10, 20),
        parent=Element("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = {
        "geo-elem-query": {
            "element": {"name": "location", "ns": ""},
            "parent": {"name": "place", "ns": ""},
            "fragment-scope": "properties",
            "geo-option": ["units=miles"],
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoElementQuery(
        Element("location"),
        Point(10, 20),
        parent=Element("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geo-elem-query>"
        '<parent name="place" ns=""/>'
        '<element name="location" ns=""/>'
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
        "</geo-elem-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
