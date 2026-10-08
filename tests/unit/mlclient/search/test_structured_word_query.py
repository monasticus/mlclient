"""Test WordQuery through the public structured-query API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import (
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
    WordQuery,
)


def test_word_query_json_preserves_three_targets():
    query = WordQuery([Element("title"), Element("label"), Element("body")], "blue")
    assert query.serialize() == {
        "word-query": {
            "element": [
                {"name": "title", "ns": ""},
                {"name": "label", "ns": ""},
                {"name": "body", "ns": ""},
            ],
            "text": ["blue"],
        },
    }


def test_word_query_serializes_to_json():
    query = WordQuery(
        [Element("title"), Element("label")],
        ["blue", "green"],
        attribute=[Attribute("name"), Attribute("alt")],
        options=["case-sensitive"],
        weight=2,
        fragment_scope="documents",
    )
    expected = {
        "word-query": {
            "element": [{"name": "title", "ns": ""}, {"name": "label", "ns": ""}],
            "attribute": [{"name": "name", "ns": ""}, {"name": "alt", "ns": ""}],
            "fragment-scope": "documents",
            "text": ["blue", "green"],
            "term-option": ["case-sensitive"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_word_query_serializes_to_xml():
    query = WordQuery(
        [Element("title"), Element("label")],
        ["blue", "green"],
        attribute=[Attribute("name"), Attribute("alt")],
        options=["case-sensitive"],
        weight=2,
        fragment_scope="documents",
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<word-query>"
        '<element name="title" ns="" />'
        '<element name="label" ns="" />'
        '<attribute name="name" ns="" />'
        '<attribute name="alt" ns="" />'
        "<fragment-scope>documents</fragment-scope>"
        "<text>blue</text>"
        "<text>green</text>"
        "<term-option>case-sensitive</term-option>"
        "<weight>2</weight>"
        "</word-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_word_query_requires_target():
    with pytest.raises(ValueError, match=r".+") as exc:
        WordQuery([], "blue")

    assert str(exc.value) == "Use one non-empty target kind."


def test_word_query_rejects_mixed_target_kinds():
    with pytest.raises(ValueError, match=r".+") as exc:
        WordQuery([Element("title"), JsonProperty("title")], "blue")

    assert str(exc.value) == "Use one non-empty target kind."


def test_word_query_rejects_path_target():
    with pytest.raises(TypeError, match=r".+") as exc:
        WordQuery(PathIndex("/title"), "blue")

    assert str(exc.value) == (
        "Targets must be Element, JsonProperty or Field instances."
    )


def test_word_query_rejects_json_attribute():
    with pytest.raises(ValueError, match=r".+") as exc:
        WordQuery(JsonProperty("title"), "blue", attribute=Attribute("name"))

    assert str(exc.value) == ("Attribute selectors require Element targets.")


def test_word_query_rejects_invalid_fragment_scope():
    with pytest.raises(ValueError, match=r".+") as exc:
        WordQuery(Element("title"), "blue", fragment_scope="locks")

    assert str(exc.value) == ("Fragment scope must be documents or properties.")


def test_word_query_with_defaults():

    query = WordQuery(JsonProperty("title"), "blue")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<word-query>"
        "<json-property>title</json-property>"
        "<text>blue</text>"
        "</word-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_word_query_with_field():

    query = WordQuery(Field("title"), "blue")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<word-query>"
        '<field name="title" />'
        "<text>blue</text>"
        "</word-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
