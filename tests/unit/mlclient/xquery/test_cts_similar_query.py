"""Public compilation and native serialization of SimilarQuery."""

from xml.etree.ElementTree import tostring


import pytest

from mlclient.xquery import FunctionCall, SimilarQuery, cts, fn


def test_distinctive_term_thresholds():
    options = (
        '<options xmlns="cts:distinctive-terms"><min-val>1</min-val>'
        "<min-weight>2</min-weight><complete>true</complete></options>"
    )
    query = cts.similar_query(
        None, options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    assert query.to_json() == {
        "similarQuery": {
            "options": {
                "minVal": 1,
                "minWeight": 2,
                "complete": True,
            },
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:similar-query xmlns:cts="http://marklogic.com/cts" '
        'xmlns:ns1="cts:distinctive-terms"><ns1:options xmlns="cts:distinctive-terms">'
        "<ns1:min-val>1</ns1:min-val><ns1:min-weight>2</ns1:min-weight>"
        "<ns1:complete>true</ns1:complete></ns1:options></cts:similar-query>"
    )


def test_distinctive_term_options():
    options = (
        '<options xmlns="cts:distinctive-terms"><max-terms>20</max-terms>'
        "<score>logtf</score></options>"
    )
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    assert query.to_json() == {
        "similarQuery": {
            "nodes": ["<report>blue</report>"],
            "options": {"maxTerms": 20, "score": "logtf"},
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:similar-query xmlns:cts="http://marklogic.com/cts" '
        'xmlns:ns1="cts:distinctive-terms"><cts:node><report>blue</report>'
        '</cts:node><ns1:options xmlns="cts:distinctive-terms">'
        "<ns1:max-terms>20</ns1:max-terms>"
        "<ns1:score>logtf</ns1:score></ns1:options></cts:similar-query>"
    )


def test_comments_in_distinctive_term_options_are_skipped():
    options = (
        '<options xmlns="cts:distinctive-terms"><!-- tuned -->'
        "<max-terms>20</max-terms><?review later?></options>"
    )
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )

    assert query.to_json()["similarQuery"]["options"] == {"maxTerms": 20}


def test_unsupported_distinctive_term_options():
    options = '<options xmlns="cts:distinctive-terms"><unknown>true</unknown></options>'
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    with pytest.raises(
        ValueError,
        match="Unsupported local CTS distinctive-term option",
    ) as error:
        query.serialize()
    assert str(error.value) == (

        "cts:similar-query: options: Unsupported local CTS distinctive-term "
        "option: {cts:distinctive-terms}unknown"

    )


def test_non_xml_options():
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", ('{"maxTerms":20}',)),
    )
    with pytest.raises(ValueError, match="CTS similar options must be an XML") as error:
        query.serialize()
    assert str(error.value) == (
        "cts:similar-query: options: CTS similar options must be an XML "
        "cts:distinctive-terms options element."
    )


def test_computed_options_require_evaluation():
    query = cts.similar_query(None, options=fn.doc("/options.xml"))
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:similar-query: options: CTS node argument requires a literal "
        "xdmp:unquote call or server evaluation."
    )


def test_compilation():
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    assert isinstance(query, SimilarQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string exte'
            "rnal;\ndeclare variable $v1 as xs:integer external;\ncts:similar"
            "-query(xdmp:unquote($v0), xs:double($v1))"
        ),
        {"v0": "<report>blue</report>", "v1": "2"},
    )


def test_serialization():
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    expected = {"similarQuery": {"nodes": ["<report>blue</report>"], "weight": 2}}
    assert query.serialize() == expected
    assert query.to_json() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.serialize("xml"), encoding="unicode") == (
        '<cts:similar-query xmlns:cts="http://marklogic.com/cts" weight="'
        '2"><cts:node><report>blue</report></cts:node></cts:similar-query'
        ">"
    )
