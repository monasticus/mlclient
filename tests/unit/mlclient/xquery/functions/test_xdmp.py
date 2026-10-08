from __future__ import annotations

import pytest

from mlclient.xquery import cts, fn, xdmp

from tests.utils.resources import discover_xqy_compilation_cases


@pytest.mark.parametrize(
    "case",
    discover_xqy_compilation_cases(__file__),
    ids=lambda case: case.name,
)
def test_xdmp(case):
    case.assert_matches()


@pytest.mark.parametrize(
    ("expression", "expected_code", "expected_variables"),
    [
        (
            xdmp.unquote('{"label":"blue"}'),
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string external;\n'
            'xdmp:unquote($v0)',
            {"v0": '{"label":"blue"}'},
        ),
        (
            xdmp.unquote("<report/>", default_namespace="urn:reports"),
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string external;\n'
            'declare variable $v1 as xs:string external;\nxdmp:unquote($v0, $v1)',
            {"v0": "<report/>", "v1": "urn:reports"},
        ),
        (
            xdmp.unquote("{}", options=["repair-none", "format-json"]),
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string external;\n'
            'declare variable $v1 as xs:string external;\n'
            'declare variable $v2 as xs:string external;\n'
            'xdmp:unquote($v0, (), ($v1, $v2))',
            {"v0": "{}", "v1": "repair-none", "v2": "format-json"},
        ),
        (
            xdmp.unquote(
                fn.string("<report/>"), default_namespace="", options="repair-none",
            ),
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string external;\n'
            'declare variable $v1 as xs:string external;\n'
            'declare variable $v2 as xs:string external;\n'
            'xdmp:unquote(fn:string($v0), $v1, $v2)',
            {"v0": "<report/>", "v1": "", "v2": "repair-none"},
        ),
    ],
)
def test_unquote_compilation(expression, expected_code, expected_variables):
    assert expression.compile() == (expected_code, expected_variables)


def test_unquote_literal_remains_locally_serializable():
    query = cts.similar_query(xdmp.unquote('{"label":"blue","count":2}'))
    assert query.to_json() == {
        "similarQuery": {"nodes": [{"label": "blue", "count": 2}]},
    }
