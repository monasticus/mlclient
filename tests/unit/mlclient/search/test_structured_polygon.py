"""Test Polygon through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import Point, Polygon


def test_serializes_to_json():
    query = Polygon([Point(10, 20), Point(11, 21), Point(10, 22)])
    expected = {
        "polygon": [
            {
                "point": [
                    {"latitude": 10, "longitude": 20},
                    {"latitude": 11, "longitude": 21},
                    {"latitude": 10, "longitude": 22},
                ],
            },
        ],
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = Polygon([Point(10, 20), Point(11, 21), Point(10, 22)])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<polygon>"
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>20"
        "</longitude>"
        "</point>"
        "<point>"
        "<latitude>11"
        "</latitude>"
        "<longitude>21"
        "</longitude>"
        "</point>"
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>22"
        "</longitude>"
        "</point>"
        "</polygon>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
