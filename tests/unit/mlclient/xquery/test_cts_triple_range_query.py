"""Public compilation and native serialization of TripleRangeQuery."""

from xml.etree.ElementTree import tostring


import pytest

from mlclient.xquery import FunctionCall, TripleRangeQuery, cts, fn


def test_three_operators():
    query = cts.triple_range_query("blue", "label", 2, operator=["!=", "=", ">"])
    assert query.to_json() == {
        "tripleRangeQuery": {
            "subjectOperator": "!=",
            "predicateOperator": "=",
            "objectOperator": ">",
            "subject": [
                {
                    "datatype": "http://www.w3.org/2001/XMLSchema#string",
                    "value": "blue",
                },
            ],
            "predicate": [
                {
                    "datatype": "http://www.w3.org/2001/XMLSchema#string",
                    "value": "label",
                },
            ],
            "object": [
                {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "value": 2},
            ],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:triple-range-query xmlns:cts="http://marklogic.com/cts" '
        'subject-operator="!=" predicate-operator="=" object-operator="&gt;">'
        '<cts:subject datatype="http://www.w3.org/2001/XMLSchema#string">blue'
        '</cts:subject><cts:predicate datatype="http://www.w3.org/2001/XMLSchema#string">'
        'label</cts:predicate><cts:object datatype="http://www.w3.org/2001/XMLSchema#integer">'
        "2</cts:object></cts:triple-range-query>"
    )


def test_invalid_operator_count():
    query = cts.triple_range_query(None, None, 2, operator=["=", "="])
    with pytest.raises(
        ValueError, match="CTS triple operator requires one or three values",
    ) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:triple-range-query: CTS triple operator requires one or three values."
    )


def test_computed_values_require_evaluation():
    query = cts.triple_range_query(None, None, fn.doc("/value.xml"))
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (

        "cts:triple-range-query: object: CTS value argument requires server "
        "evaluation, got fn:doc('/value.xml')."

    )


def test_default_operators():
    query = cts.triple_range_query(None, None, 2)
    assert query.to_json() == {
        "tripleRangeQuery": {
            "object": [
                {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "value": 2},
            ],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:triple-range-query xmlns:cts="http://marklogic.com/cts">'
        '<cts:object datatype="http://www.w3.org/2001/XMLSchema#integer">2'
        "</cts:object></cts:triple-range-query>"
    )


def test_compilation():
    query = cts.triple_range_query(
        FunctionCall("sem:iri", ("urn:r",)),
        FunctionCall("sem:iri", ("urn:p",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    )
    assert isinstance(query, TripleRangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string exte'
            "rnal;\ndeclare variable $v1 as xs:string external;\ndeclare vari"
            "able $v2 as xs:integer external;\ndeclare variable $v3 as xs:boo"
            "lean external;\ndeclare variable $v4 as xs:string external;\ndec"
            "lare variable $v5 as xs:string external;\ndeclare variable $v6 a"
            "s xs:string external;\ndeclare variable $v7 as xs:integer extern"
            "al;\ncts:triple-range-query(sem:iri($v0), sem:iri($v1), ($v2, $v"
            "3, $v4), $v5, $v6, xs:double($v7))"
        ),
        {
            "v0": "urn:r",
            "v1": "urn:p",
            "v2": "2",
            "v3": True,
            "v4": "blue",
            "v5": ">",
            "v6": "cached",
            "v7": "2",
        },
    )


def test_serialization():
    query = cts.triple_range_query(
        FunctionCall("sem:iri", ("urn:r",)),
        FunctionCall("sem:iri", ("urn:p",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    )
    expected = {
        "tripleRangeQuery": {
            "objectOperator": ">",
            "subject": ["urn:r"],
            "predicate": ["urn:p"],
            "object": [
                {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "value": 2},
                {"datatype": "http://www.w3.org/2001/XMLSchema#boolean", "value": True},
                {
                    "datatype": "http://www.w3.org/2001/XMLSchema#string",
                    "value": "blue",
                },
            ],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.to_json() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.serialize("xml"), encoding="unicode") == (
        '<cts:triple-range-query xmlns:cts="http://marklogic.com/cts" obj'
        'ect-operator="&gt;" weight="2"><cts:subject>urn:r</cts:subject><'
        'cts:predicate>urn:p</cts:predicate><cts:object datatype="http://'
        'www.w3.org/2001/XMLSchema#integer">2</cts:object><cts:object dat'
        'atype="http://www.w3.org/2001/XMLSchema#boolean">true</cts:objec'
        't><cts:object datatype="http://www.w3.org/2001/XMLSchema#string"'
        ">blue</cts:object><cts:option>cached</cts:option></cts:triple-ra"
        "nge-query>"
    )
