"""Test structured-query target serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import Attribute


def test_attribute_serializes_to_json():
    query = Attribute("status", "https://example.com/example")
    expected = {"attribute": {"name": "status", "ns": "https://example.com/example"}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_attribute_serializes_to_xml():
    query = Attribute("status", "https://example.com/example")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<attribute name="status" ns="https://example.com/example" />'
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
