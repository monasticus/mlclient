"""Test GeoRegionConstraintQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import GeoRegionConstraintQuery, Point


def test_serializes_to_json():
    query = GeoRegionConstraintQuery(
        "location",
        Point(10, 20),
        operator="intersects",
        weight=2,
    )
    expected = {
        "geo-region-constraint-query": {
            "constraint-name": "location",
            "geospatial-operator": "intersects",
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoRegionConstraintQuery(
        "location",
        Point(10, 20),
        operator="intersects",
        weight=2,
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<geo-region-constraint-query>"
        "<constraint-name>location"
        "</constraint-name>"
        "<geospatial-operator>intersects"
        "</geospatial-operator>"
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>20"
        "</longitude>"
        "</point>"
        "<weight>2"
        "</weight>"
        "</geo-region-constraint-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
