"""Test ContainerQuery through the public structured-query API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import ContainerQuery, Element, Field, TermQuery


def test_container_query_serializes_to_json():
    query = ContainerQuery(
        Element("section", "urn:example"),
        TermQuery("blue"),
        fragment_scope="properties",
    )
    expected = {
        "container-query": {
            "element": {"name": "section", "ns": "urn:example"},
            "fragment-scope": "properties",
            "term-query": {"text": ["blue"]},
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_container_query_serializes_to_xml():
    query = ContainerQuery(
        Element("section", "urn:example"),
        TermQuery("blue"),
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<container-query>"
        '<element name="section" ns="urn:example" />'
        "<fragment-scope>properties</fragment-scope>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</container-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_container_query_rejects_field_target():
    with pytest.raises(TypeError, match=r".+") as exc:
        ContainerQuery(Field("body"), TermQuery("blue"))

    assert str(exc.value) == (
        "Container queries require element or JSON property targets."
    )
