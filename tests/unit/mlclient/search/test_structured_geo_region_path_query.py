"""Test GeoRegionPathQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point


def test_serializes_to_json():
    query = GeoRegionPathQuery(
        PathIndex("/place/region"),
        Point(10, 20),
        operator="intersects",
        coord="wgs84",
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = {
        "geo-region-path-query": {
            "coord": "wgs84",
            "path-index": {"text": "/place/region"},
            "geospatial-operator": "intersects",
            "fragment-scope": "properties",
            "geo-option": ["units=miles"],
            "point": [{"latitude": 10, "longitude": 20}],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = GeoRegionPathQuery(
        PathIndex("/place/region"),
        Point(10, 20),
        operator="intersects",
        coord="wgs84",
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<geo-region-path-query coord="wgs84">'
        "<path-index>/place/region"
        "</path-index>"
        "<geospatial-operator>intersects"
        "</geospatial-operator>"
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
        "</geo-region-path-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
