"""Test Box through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import Box


def test_serializes_to_json():
    query = Box(5, 15, 25, 35)
    expected = {"box": [{"south": 5, "west": 15, "north": 25, "east": 35}]}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = Box(5, 15, 25, 35)
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<box>"
        "<south>5"
        "</south>"
        "<west>15"
        "</west>"
        "<north>25"
        "</north>"
        "<east>35"
        "</east>"
        "</box>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
