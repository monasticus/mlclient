"""Test Point through its public API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import Point


@pytest.mark.parametrize(
    ("latitude", "longitude", "message"),
    [
        (float("inf"), 20, "Point.latitude must be finite."),
        (10, float("nan"), "Point.longitude must be finite."),
    ],
)
def test_point_rejects_nonfinite_coordinate(latitude, longitude, message):
    with pytest.raises(ValueError, match="must be finite") as exc:
        Point(latitude, longitude)
    assert str(exc.value) == message


def test_serializes_to_json():
    query = Point(10, 20)
    expected = {"point": [{"latitude": 10, "longitude": 20}]}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = Point(10, 20)
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<point>"
        "<latitude>10"
        "</latitude>"
        "<longitude>20"
        "</longitude>"
        "</point>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
