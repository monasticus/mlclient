"""Test GeoJsonPropertyQuery through its public API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import GeoJsonPropertyQuery, JsonProperty, Point


def test_serializes_to_json():
    query = GeoJsonPropertyQuery(
        JsonProperty("location"),
        Point(10, 20),
        parent=JsonProperty("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = {
        "geo-json-property-query": {
            "json-property": "location",
            "parent-property": "place",
            "fragment-scope": "properties",
            "geo-option": ["units=miles"],
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoJsonPropertyQuery(
        JsonProperty("location"),
        Point(10, 20),
        parent=JsonProperty("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geo-json-property-query>"
        "<parent-property>place"
        "</parent-property>"
        "<json-property>location"
        "</json-property>"
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
        "</geo-json-property-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_geo_json_property_query_rejects_a_property_name_string():
    with pytest.raises(TypeError) as exc:
        GeoJsonPropertyQuery("location", Point(10, 20))

    assert str(exc.value) == (
        "Geospatial JSON property selectors must be JsonProperty instances."
    )
