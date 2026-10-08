"""Test ValueQuery through the public structured-query API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import Attribute, Element, JsonProperty, ValueQuery


def test_value_query_serializes_to_json():
    query = ValueQuery(
        JsonProperty("active"),
        True,
        node_type="boolean",
        options=["exact"],
        weight=2,
        fragment_scope="documents",
    )
    expected = {
        "value-query": {
            "type": "boolean",
            "json-property": "active",
            "fragment-scope": "documents",
            "text": ["true"],
            "term-option": ["exact"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_value_query_serializes_to_xml():
    query = ValueQuery(
        JsonProperty("active"),
        True,
        node_type="boolean",
        options=["exact"],
        weight=2,
        fragment_scope="documents",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<value-query type="boolean">'
        "<json-property>active</json-property>"
        "<fragment-scope>documents</fragment-scope>"
        "<text>true</text>"
        "<term-option>exact</term-option>"
        "<weight>2</weight>"
        "</value-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_value_query_with_null():
    query = ValueQuery(JsonProperty("count"), "", node_type="null")
    expected = ElementTree.fromstring(
        '<value-query xmlns="http://marklogic.com/appservices/search" type="null">'
        "<json-property>count</json-property>"
        "<text />"
        "</value-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_value_query_with_number():
    query = ValueQuery(JsonProperty("count"), 7, node_type="number")
    expected = ElementTree.fromstring(
        '<value-query xmlns="http://marklogic.com/appservices/search" type="number">'
        "<json-property>count</json-property>"
        "<text>7</text>"
        "</value-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_value_query_rejects_invalid_node_type():
    with pytest.raises(ValueError, match=r".+") as exc:
        ValueQuery(JsonProperty("active"), True, node_type="date")

    assert str(exc.value) == (
        "JSON node type must be string, boolean, null, or number."
    )


def test_value_query_with_element_attribute():

    query = ValueQuery(Element("label"), "blue", attribute=Attribute("color"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<value-query>"
        '<element name="label" ns="" />'
        '<attribute name="color" ns="" />'
        "<text>blue</text>"
        "</value-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
