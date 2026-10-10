"""Test structured-query target serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import Field


def test_field_serializes_to_json():
    query = Field("body", collation="http://marklogic.com/collation/")
    expected = {
        "field": {"name": "body", "collation": "http://marklogic.com/collation/"},
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_field_serializes_to_xml():
    query = Field("body", collation="http://marklogic.com/collation/")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<field name="body" collation="http://marklogic.com/collation/" />'
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_field_without_collation():
    query = Field("body")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<field name="body" />'
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
