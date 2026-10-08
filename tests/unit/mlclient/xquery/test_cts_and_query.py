"""Intersection serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.xquery import AndQuery, cts, fn


def test_and_query():
    query = cts.and_query(
        [
            cts.word_query("blue", options="lang=en"),
            cts.collection_query("reports"),
        ],
        options="ordered",
    )
    assert isinstance(query, AndQuery)
    assert query.serialize() == {
        "andQuery": {
            "queries": [
                {"wordQuery": {"text": ["blue"], "options": ["lang=en"]}},
                {"collectionQuery": {"uris": ["reports"]}},
            ],
            "options": ["ordered"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:and-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:word-query><cts:text>blue</cts:text>"
        "<cts:option>lang=en</cts:option></cts:word-query>"
        "<cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query>"
        "<cts:option>ordered</cts:option></cts:and-query>"
    )
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "declare variable $v3 as xs:string external;\n"
        "cts:and-query((cts:word-query($v0, $v1), cts:collection-query($v2)), $v3)",
        {"v0": "blue", "v1": "lang=en", "v2": "reports", "v3": "ordered"},
    )


def test_and_query_implicit_words():
    assert cts.and_query(["blue"]).serialize() == {
        "andQuery": {"queries": [{"wordQuery": {"text": ["blue"]}}]},
    }


def test_and_query_empty():
    assert cts.and_query([]).serialize() == {"andQuery": {}}


def test_and_query_unresolved_subquery():
    with pytest.raises(TypeError) as error:
        cts.and_query(fn.string("blue")).serialize()
    assert str(error.value) == (

        "cts:and-query: queries: CTS subquery requires server evaluation, got "
        "fn:string('blue')."


    )


def test_and_query_invalid_options():
    with pytest.raises(
        ValueError,
        match="are not and-query options",
    ) as error:
        cts.and_query([], options="bogus")
    assert str(error.value) == (
        "options ['bogus'] are not and-query options; "
        "use at most one of ordered, unordered"
    )
