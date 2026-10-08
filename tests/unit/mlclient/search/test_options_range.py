"""Range options reuse the public structured-query targets."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.search.options import Range
from mlclient.search.structured import (
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
)

NS = "http://marklogic.com/appservices/search"


def test_element_range():
    index = Range(Element("price", "urn:products"), "xs:decimal")

    assert index.to_json() == {
        "range": {
            "type": "xs:decimal",
            "element": {"name": "price", "ns": "urn:products"},
        },
    }
    assert tostring(index.to_xml(), encoding="unicode") == (
        f'<search:range xmlns:search="{NS}" type="xs:decimal">'
        '<search:element name="price" ns="urn:products" /></search:range>'
    )


def test_attribute_range_with_collation():
    index = Range(
        Element("product"), attribute=Attribute("category"), collation="urn:collation",
    )

    assert index.to_json() == {
        "range": {
            "type": "xs:string",
            "collation": "urn:collation",
            "element": {"name": "product", "ns": ""},
            "attribute": {"name": "category", "ns": ""},
        },
    }
    assert tostring(index.to_xml(), encoding="unicode") == (
        f'<search:range xmlns:search="{NS}" type="xs:string" collation="urn:collation">'
        '<search:element name="product" ns="" />'
        '<search:attribute name="category" ns="" /></search:range>'
    )


def test_json_property_range():
    index = Range(JsonProperty("price"), "xs:decimal")

    assert index.to_json() == {
        "range": {"type": "xs:decimal", "json-property": "price"},
    }
    assert tostring(index.to_xml(), encoding="unicode") == (
        f'<search:range xmlns:search="{NS}" type="xs:decimal">'
        "<search:json-property>price</search:json-property></search:range>"
    )


def test_field_range():
    index = Range(Field("category", "urn:collation"))

    assert index.to_json() == {
        "range": {
            "type": "xs:string",
            "field": {"name": "category", "collation": "urn:collation"},
        },
    }
    assert tostring(index.to_xml(), encoding="unicode") == (
        f'<search:range xmlns:search="{NS}" type="xs:string">'
        '<search:field name="category" collation="urn:collation" /></search:range>'
    )


def test_path_range():
    index = Range(PathIndex("/p:product/p:price", {"p": "urn:products"}), "xs:decimal")

    assert index.to_json() == {
        "range": {
            "type": "xs:decimal",
            "path-index": {
                "namespaces": {"p": "urn:products"},
                "text": "/p:product/p:price",
            },
        },
    }
    assert tostring(index.to_xml(), encoding="unicode") == (
        f'<search:range xmlns:search="{NS}" type="xs:decimal">'
        '<search:path-index xmlns:p="urn:products">/p:product/p:price'
        "</search:path-index></search:range>"
    )


def test_unsupported_range_target():
    with pytest.raises(TypeError) as error:
        Range("price").to_json()

    assert str(error.value) == (
        "range target must be an Element, Field, JsonProperty or PathIndex"
    )


def test_attribute_on_non_element_target():
    with pytest.raises(TypeError) as error:
        Range(JsonProperty("product"), attribute=Attribute("category")).to_xml()

    assert (
        str(error.value)
        == "range attribute requires an Element target and an Attribute"
    )


def test_invalid_attribute():
    with pytest.raises(TypeError) as error:
        Range(Element("product"), attribute="category").to_json()

    assert (
        str(error.value)
        == "range attribute requires an Element target and an Attribute"
    )
