"""Runtime CTS queries compile but cannot be described without evaluation."""

import pytest

from mlclient.xquery import FunctionCall, RuntimeQuery, cts


def test_serialization_compiles():
    query = cts.parse("blue AND green")
    assert isinstance(query, RuntimeQuery)
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "cts:parse($v0)",
        {"v0": "blue AND green"},
    )


def test_serialization_with_bindings_compiles():
    query = cts.parse("blue", bindings=FunctionCall("map:map"))
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "cts:parse($v0, map:map())",
        {"v0": "blue"},
    )


def test_query_compiles():
    source = '{"wordQuery":{"text":["blue"]}}'
    query = cts.query(FunctionCall("xdmp:unquote", (source,)))
    assert isinstance(query, RuntimeQuery)
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "cts:query(xdmp:unquote($v0))",
        {"v0": source},
    )


def test_serializes_to_json_requires_evaluation():
    with pytest.raises(TypeError) as error:
        cts.parse("blue").to_json()
    assert str(error.value) == (
        "runtime query: CTS runtime query requires server evaluation before "
        "serialization."
    )


def test_query_xml_requires_evaluation():
    with pytest.raises(TypeError) as error:
        cts.query(FunctionCall("fn:doc", ("/query.xml",))).to_xml()
    assert str(error.value) == (
        "runtime query: CTS runtime query requires server evaluation before "
        "serialization."
    )


def test_runtime_query_composes():
    query = cts.and_query([cts.parse("blue"), cts.collection_query("reports")])
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "cts:and-query((cts:parse($v0), cts:collection-query($v1)))",
        {"v0": "blue", "v1": "reports"},
    )
