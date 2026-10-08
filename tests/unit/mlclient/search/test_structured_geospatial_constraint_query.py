"""Test GeospatialConstraintQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import GeospatialConstraintQuery, Point


def test_serializes_to_json():
    query = GeospatialConstraintQuery("location", Point(10, 20), text="nearby")
    expected = {
        "geospatial-constraint-query": {
            "constraint-name": "location",
            "point": [{"latitude": 10, "longitude": 20}],
            "text": ["nearby"],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeospatialConstraintQuery("location", Point(10, 20), text="nearby")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geospatial-constraint-query>"
        "<constraint-name>location"
        "</constraint-name>"
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>20"
        "</longitude>"
        "</point>"
        "<text>nearby"
        "</text>"
        "</geospatial-constraint-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
