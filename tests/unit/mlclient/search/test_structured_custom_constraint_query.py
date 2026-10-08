"""Test custom-constraint-query serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import CustomConstraintQuery


def test_serializes_to_json():
    query = CustomConstraintQuery("custom", ["blue", "green"])
    expected = {
        "custom-constraint-query": {
            "constraint-name": "custom",
            "text": ["blue", "green"],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = CustomConstraintQuery("custom", ["blue", "green"])
    expected = ElementTree.fromstring(
        '<custom-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>custom</constraint-name><text>blue</text><text>green</text>"
        "</custom-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
