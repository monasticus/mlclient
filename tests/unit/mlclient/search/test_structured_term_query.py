"""Test TermQuery through the public structured-query API."""

from decimal import Decimal
from xml.etree import ElementTree

import pytest

from mlclient.search.structured import Element, RangeQuery, TermQuery


def test_term_query_serializes_to_json():
    query = TermQuery(
        ["blue", "green"],
        weight=2,
        options=["case-sensitive", "unstemmed"],
    )
    expected = {
        "term-query": {
            "text": ["blue", "green"],
            "weight": 2,
            "term-option": ["case-sensitive", "unstemmed"],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_term_query_serializes_to_xml():
    query = TermQuery(
        ["blue", "green"],
        weight=2,
        options=["case-sensitive", "unstemmed"],
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<term-query>"
        "<text>blue</text>"
        "<text>green</text>"
        "<weight>2</weight>"
        "<term-option>case-sensitive</term-option>"
        "<term-option>unstemmed</term-option>"
        "</term-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_term_query_escapes_text():
    query = TermQuery("a < b & c")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<term-query>"
        "<text>a &lt; b &amp; c</text>"
        "</term-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


@pytest.mark.parametrize("weight", [Decimal("NaN"), Decimal("Infinity"), float("-inf")])
def test_term_query_rejects_a_non_finite_weight(weight):
    with pytest.raises(ValueError, match="must be finite") as exc:
        TermQuery("blue", weight=weight)

    assert str(exc.value) == "TermQuery.weight must be finite."


def test_range_query_values_may_be_non_finite():
    query = RangeQuery(Element("price"), Decimal("NaN"), operator="LT")

    assert query.to_json()["range-query"]["value"] == "NaN"
