"""Test GeoJsonPropertyPairQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import GeoJsonPropertyPairQuery, JsonProperty, Point


def test_serializes_to_json():
    query = GeoJsonPropertyPairQuery(
        JsonProperty("place"),
        JsonProperty("lat"),
        JsonProperty("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = {
        "geo-json-property-pair-query": {
            "parent-property": "place",
            "lat-property": "lat",
            "lon-property": "lon",
            "fragment-scope": "properties",
            "geo-option": ["units=miles"],
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoJsonPropertyPairQuery(
        JsonProperty("place"),
        JsonProperty("lat"),
        JsonProperty("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geo-json-property-pair-query>"
        "<parent-property>place"
        "</parent-property>"
        "<lat-property>lat"
        "</lat-property>"
        "<lon-property>lon"
        "</lon-property>"
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
        "</geo-json-property-pair-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
