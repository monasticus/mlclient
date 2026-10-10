"""Test structured-query target serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import Element


def test_element_serializes_to_json():
    query = Element("label", "https://example.com/example")
    expected = {"element": {"name": "label", "ns": "https://example.com/example"}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_element_serializes_to_xml():
    query = Element("label", "https://example.com/example")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<element name="label" ns="https://example.com/example" />'
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
