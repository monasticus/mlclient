"""Test structured-query target serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import JsonProperty


def test_json_property_serializes_to_json():
    query = JsonProperty("title")
    expected = {"json-property": "title"}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_json_property_serializes_to_xml():
    query = JsonProperty("title")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<json-property>title</json-property>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
