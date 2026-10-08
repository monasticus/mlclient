"""Native word-query serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.xquery import CtsQuery, FunctionCall, WordQuery, cts, fn


def test_word_query():
    query = cts.word_query("blue", options="lang=en")
    assert isinstance(query, WordQuery)
    assert isinstance(query, CtsQuery)
    assert query.serialize() == {
        "wordQuery": {"text": ["blue"], "options": ["lang=en"]},
    }
    assert tostring(query.serialize("xml"), encoding="unicode") == (
        '<cts:word-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:text>blue</cts:text><cts:option>lang=en</cts:option></cts:word-query>"
    )
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "cts:word-query($v0, $v1)",
        {"v0": "blue", "v1": "lang=en"},
    )


def test_word_query_exact():
    query = cts.word_query(["blue", "green"], options=["lang=FR", "exact"], weight=2)
    assert query.to_json() == {
        "wordQuery": {
            "text": ["blue", "green"],
            "options": ["lang=FR", "exact"],
            "weight": 2,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:word-query xmlns:cts="http://marklogic.com/cts" weight="2">'
        "<cts:text>blue</cts:text>"
        "<cts:text>green</cts:text>"
        "<cts:option>lang=FR</cts:option>"
        "<cts:option>exact</cts:option></cts:word-query>"
    )


def test_word_query_without_language():
    query = cts.word_query("blue")
    assert query.serialize() == {"wordQuery": {"text": ["blue"]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:word-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:text>blue</cts:text></cts:word-query>"
    )


def test_word_query_options_keep_supplied_order():
    query = cts.word_query("blue", options=["unstemmed", "case-insensitive", "lang=en"])
    assert query.serialize() == {
        "wordQuery": {
            "text": ["blue"],
            "options": ["unstemmed", "case-insensitive", "lang=en"],
        },
    }


def test_word_query_options_are_not_validated_locally():
    query = cts.word_query("blue", options=["lang=eng", "synonym", "synonym", "bogus"])
    assert query.serialize() == {
        "wordQuery": {
            "text": ["blue"],
            "options": ["lang=eng", "synonym", "synonym", "bogus"],
        },
    }


def test_word_query_empty():
    query = cts.word_query(None, options="lang=en")
    assert query.serialize() == {"wordQuery": {"options": ["lang=en"]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:word-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:option>lang=en</cts:option></cts:word-query>"
    )


def test_word_query_weight():
    query = cts.word_query("blue", weight=0.5)
    assert query.serialize() == {"wordQuery": {"text": ["blue"], "weight": 0.5}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:word-query xmlns:cts="http://marklogic.com/cts" weight="0.5">'
        "<cts:text>blue</cts:text></cts:word-query>"
    )


def test_word_query_default_weight_is_retained():
    assert cts.word_query("blue", weight=1).serialize() == {
        "wordQuery": {"text": ["blue"], "weight": 1},
    }


def test_word_query_out_of_range_weight_is_retained():
    assert cts.word_query("blue", weight=100).serialize() == {
        "wordQuery": {"text": ["blue"], "weight": 100},
    }


def test_word_query_small_weight():
    assert tostring(cts.word_query("blue", weight=0.00001).to_xml()) == (
        b'<cts:word-query xmlns:cts="http://marklogic.com/cts" weight="0.00001">'
        b"<cts:text>blue</cts:text></cts:word-query>"
    )


def test_word_query_scientific_weight():
    assert tostring(cts.word_query("blue", weight=0.0000001).to_xml()) == (
        b'<cts:word-query xmlns:cts="http://marklogic.com/cts" weight="1.0E-7">'
        b"<cts:text>blue</cts:text></cts:word-query>"
    )


def test_word_query_unresolved_weight():
    with pytest.raises(TypeError) as error:
        cts.word_query("blue", weight=fn.last()).serialize()
    assert str(error.value) == (

        "cts:word-query: weight: CTS numeric argument requires server evaluation, "
        "got fn:last()."

    )


def test_word_query_unresolved_text():
    with pytest.raises(TypeError) as error:
        cts.word_query(fn.string("blue")).serialize()
    assert str(error.value) == (

        "cts:word-query: text: CTS string argument requires server evaluation, got "
        "fn:string('blue')."

    )


def test_word_query_invalid_format():
    with pytest.raises(ValueError, match="Query format must be json or xml") as error:
        cts.word_query("blue").serialize("yaml")
    assert str(error.value) == "cts:word-query: Query format must be json or xml."


def test_word_query_nonfinite_weight():
    with pytest.raises(ValueError, match="CTS numbers must be finite") as error:
        cts.word_query("blue", weight=float("inf")).serialize()
    assert str(error.value) == (
        "cts:word-query: weight: CTS numbers must be finite for local serialization."
    )


def test_word_query_invalid_numeric_expression():
    with pytest.raises(TypeError) as error:
        cts.word_query(
            "blue",
            weight=FunctionCall("xs:double", (2, 3)),
        ).serialize()
    assert str(error.value) == (

        "cts:word-query: weight: CTS numeric argument requires server evaluation, "
        "got xs:double(2, 3)."

    )


def test_word_query_snapshot():
    texts = ["blue"]
    query = cts.word_query(texts)
    texts.append("green")
    output = query.serialize()
    output["wordQuery"]["text"].append("red")
    assert query.serialize() == {"wordQuery": {"text": ["blue"]}}


def test_word_query_combined_query():
    assert cts.word_query("blue").to_combined_query() == {
        "search": {"ctsquery": {"wordQuery": {"text": ["blue"]}}},
    }


def test_word_query_independent_json(mocker):
    mocker.patch.object(WordQuery, "to_xml", side_effect=AssertionError)
    assert cts.word_query("blue").to_json() == {"wordQuery": {"text": ["blue"]}}


def test_word_query_independent_xml(mocker):
    mocker.patch.object(WordQuery, "to_json", side_effect=AssertionError)
    assert tostring(cts.word_query("blue").to_xml()) == (
        b'<cts:word-query xmlns:cts="http://marklogic.com/cts">'
        b"<cts:text>blue</cts:text></cts:word-query>"
    )
