"""Test RangeQuery through the public structured-query API."""

from datetime import date, datetime
from decimal import Decimal
from xml.etree import ElementTree

import pytest

from mlclient.search.structured import (
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
    RangeQuery,
)


def test_range_query_serializes_to_json():
    query = RangeQuery(
        Element("price"),
        [3, 4],
        operator="EQ",
        index_type="xs:int",
        collation="urn:example",
        options=["cached"],
        weight=2,
        fragment_scope="documents",
        attribute=Attribute("amount"),
    )
    expected = {
        "range-query": {
            "type": "xs:int",
            "collation": "urn:example",
            "element": {"name": "price", "ns": ""},
            "attribute": {"name": "amount", "ns": ""},
            "fragment-scope": "documents",
            "value": ["3", "4"],
            "range-operator": "EQ",
            "range-option": "cached",
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_range_query_serializes_to_xml():
    query = RangeQuery(
        Element("price"),
        [3, 4],
        operator="EQ",
        index_type="xs:int",
        collation="urn:example",
        options=["cached"],
        weight=2,
        fragment_scope="documents",
        attribute=Attribute("amount"),
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        '<range-query type="xs:int" collation="urn:example">'
        '<element name="price" ns="" />'
        '<attribute name="amount" ns="" />'
        "<fragment-scope>documents</fragment-scope>"
        "<value>3</value>"
        "<value>4</value>"
        "<range-operator>EQ</range-operator>"
        "<range-option>cached</range-option>"
        "<weight>2</weight>"
        "</range-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_requires_value():
    with pytest.raises(ValueError, match=r".+") as exc:
        RangeQuery(Element("price"), [])

    assert str(exc.value) == "Range queries require at least one value."


def test_range_query_rejects_multiple_relational_values():
    with pytest.raises(ValueError, match=r".+") as exc:
        RangeQuery(Element("price"), [1, 2], operator="GT")

    assert str(exc.value) == "Multiple range values require EQ or NE."


def test_range_query_with_float():
    query = RangeQuery(Element("price"), 2.5, index_type="xs:double")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/search" type="xs:double">'
        '<element name="price" ns="" />'
        "<value>2.5</value>"
        "</range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_positive_infinity():
    query = RangeQuery(Element("price"), float("inf"), index_type="xs:double")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/search" type="xs:double">'
        '<element name="price" ns="" />'
        "<value>INF</value>"
        "</range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_negative_infinity():
    query = RangeQuery(Element("price"), float("-inf"), index_type="xs:double")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/search" type="xs:double">'
        '<element name="price" ns="" />'
        "<value>-INF</value>"
        "</range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_nan():
    query = RangeQuery(Element("price"), float("nan"), index_type="xs:double")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/search" type="xs:double">'
        '<element name="price" ns="" />'
        "<value>NaN</value>"
        "</range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_path_index():

    query = RangeQuery(PathIndex("/report/price"), 2, operator="LT")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/search">'
        "<path-index>/report/price</path-index>"
        "<value>2</value>"
        "<range-operator>LT</range-operator>"
        "</range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_rejects_invalid_operator():
    with pytest.raises(ValueError, match=r".+") as exc:
        RangeQuery(Element("price"), 1, operator=">")

    assert str(exc.value) == ("Range operator must be LT, LE, GT, GE, EQ, or NE.")


def test_range_query_with_defaults():
    query = RangeQuery(Element("price"), 0)
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<range-query>"
        '<element name="price" ns="" />'
        "<value>0</value>"
        "</range-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_date():

    query = RangeQuery(Element("date"), date(2026, 1, 2))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<range-query>"
        '<element name="date" ns="" />'
        "<value>2026-01-02</value>"
        "</range-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_decimal():

    query = RangeQuery(JsonProperty("price"), Decimal("2.50"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<range-query>"
        "<json-property>price</json-property>"
        "<value>2.50</value>"
        "</range-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_range_query_with_datetime():

    query = RangeQuery(Field("price"), datetime(2026, 1, 2, 3, 4, 5))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<range-query>"
        '<field name="price" />'
        "<value>2026-01-02T03:04:05</value>"
        "</range-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
