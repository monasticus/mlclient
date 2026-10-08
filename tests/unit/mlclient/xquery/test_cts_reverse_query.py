"""Public compilation and native serialization of ReverseQuery."""

from xml.etree.ElementTree import tostring


import pytest

from mlclient.xquery import FunctionCall, ReverseQuery, cts, fn


def test_computed_nodes_require_evaluation():
    query = cts.reverse_query(fn.doc("/report.xml"))
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "cts:reverse-query(fn:doc($v0))",
        {"v0": "/report.xml"},
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS node argument requires a literal "
        "xdmp:unquote call or server evaluation."
    )


def test_json_model_nodes():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ('{"label":"blue","count":2}',)),
    )
    assert query.to_json() == {
        "reverseQuery": {"nodes": [{"label": "blue", "count": 2}]},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:reverse-query xmlns:cts="http://marklogic.com/cts"><cts:node>'
        '{"label":"blue", "count":2}</cts:node></cts:reverse-query>'
    )


def test_xml_comments_and_processing_instructions():
    source = "<report><!--label--><?label blue?><label>blue</label></report>"
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:reverse-query xmlns:cts="http://marklogic.com/cts"><cts:node>'
        "<report><!--label--><?label blue?><label>blue</label></report>"
        "</cts:node></cts:reverse-query>"
    )


def test_empty_nodes():
    query = cts.reverse_query(None)
    assert query.to_json() == {"reverseQuery": {}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:reverse-query xmlns:cts="http://marklogic.com/cts" />'
    )


def test_xml_document_prolog_nodes():
    source = '<?xml version="1.0"?><?label blue?><!--report--><report>blue</report>'
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:reverse-query xmlns:cts="http://marklogic.com/cts"><cts:node>'
        "<?label blue?><!--report--><report>blue</report>"
        "</cts:node></cts:reverse-query>"
    )


def test_xml_dtd_requires_evaluation():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<!DOCTYPE report><report/>",)),
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS literal XML with a DTD requires server "
        "evaluation."
    )


def test_xml_namespace_declarations_are_preserved():
    source = '<report xmlns:r="urn:reports" kind="r:blue">blue</report>'
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:reverse-query xmlns:cts="http://marklogic.com/cts"><cts:node>'
        '<report kind="r:blue" xmlns:r="urn:reports">blue</report>'
        "</cts:node></cts:reverse-query>"
    )


def test_reserved_xml_namespace_prefix_requires_evaluation():
    source = '<report xmlns:ns0="urn:reports" kind="ns0:blue" />'
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert str(error.value) == (

        "cts:reverse-query: nodes: CTS XML namespace prefixes nsN conflict with "
        "ElementTree; use named prefixes or server evaluation."

    )


def test_json_projection_requires_evaluation():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ('{"label":"blue"}',)).xpath("*"),
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert (
        str(error.value) == (
            "cts:reverse-query: nodes: CTS JSON model-node projections require "
            "server evaluation."
        )
    )


def test_compilation():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    assert isinstance(query, ReverseQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string exte'
            "rnal;\ndeclare variable $v1 as xs:integer external;\ncts:reverse"
            "-query(xdmp:unquote($v0), xs:double($v1))"
        ),
        {"v0": "<report>blue</report>", "v1": "2"},
    )


def test_invalid_json_number():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ('{"count":NaN}',)))
    with pytest.raises(
        ValueError, match="Invalid CTS model-node JSON constant",
    ) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:reverse-query: nodes: Invalid CTS model-node JSON constant: NaN"
    )


def test_serialization():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    expected = {"reverseQuery": {"nodes": ["<report>blue</report>"], "weight": 2}}
    assert query.serialize() == expected
    assert query.to_json() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.serialize("xml"), encoding="unicode") == (
        '<cts:reverse-query xmlns:cts="http://marklogic.com/cts" weight="'
        '2"><cts:node><report>blue</report></cts:node></cts:reverse-query'
        ">"
    )
