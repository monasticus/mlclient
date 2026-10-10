"""Test Circle through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import Circle, Point


def test_serializes_to_json():
    query = Circle(3, Point(10, 20))
    expected = {
        "circle": [{"radius": 3, "point": [{"latitude": 10, "longitude": 20}]}],
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = Circle(3, Point(10, 20))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<circle>"
        "<radius>3"
        "</radius>"
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>20"
        "</longitude>"
        "</point>"
        "</circle>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
