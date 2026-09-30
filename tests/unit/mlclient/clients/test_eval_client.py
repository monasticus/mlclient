from __future__ import annotations

import json
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from mlclient.functions.xqy import XqyExpression, cts, fn, xs
from mlclient.services.eval import _LOCAL_NS
from tests.utils import resources as resources_utils
from tests.utils.expressions import StaticExpression
from tests.utils.ml_mockers import MLRespXMocker


@pytest.mark.parametrize("body", [b"", b"<html>Unavailable</html>"])
@respx.mock
def test_expression_preserves_unrecognized_http_errors(ml, body):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(503)
    ml_mocker.with_response_body(body)
    route = ml_mocker.mock_post()
    with pytest.raises(httpx.HTTPStatusError) as raised:
        ml.eval.expression(fn.count([]))
    assert raised.value.response.status_code == 503
    assert raised.value.response.content == body
    assert raised.value.request.url == route.calls.last.request.url
    assert raised.value.request.content == route.calls.last.request.content


@pytest.fixture(autouse=True)
def ml() -> MLClient:
    return MLClient()


@pytest.fixture(autouse=True)
def _setup_and_teardown(ml):
    ml.connect()

    yield

    ml.disconnect()


@respx.mock
def test_eval_preserves_bodyless_http_failure(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": "1"})
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    with pytest.raises(httpx.HTTPStatusError) as raised:
        ml.eval.xquery("1")

    assert route.call_count == 1
    assert raised.value.response.url == route.calls.last.request.url
    assert raised.value.response.status_code == 403


@respx.mock
def test_eval_raw_xquery_empty(ml):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code)

    assert resp == []


@respx.mock
def test_eval_timeout_reaches_transport_and_is_not_a_query_variable(ml):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    ml.eval.xquery(code, timeout=2)

    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@respx.mock
def test_eval_variable_named_timeout_is_sent_as_query_variable(ml):
    code = "declare variable $timeout external; $timeout"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code, "vars": '{"timeout": 30}'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "30")
    route = ml_mocker.mock_post()

    resp = ml.eval.xquery(code, variables={"timeout": 30}, timeout=2)

    assert resp == 30
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@respx.mock
def test_eval_raw_xquery_single_item(ml):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code)

    assert resp == ""


@respx.mock
def test_eval_raw_xquery_multiple_items(ml):
    code = "('',1)"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code)

    assert resp == ["", 1]


@respx.mock
def test_eval_xqy_alias(ml):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = ml.eval.xqy(code)

    assert resp == []


@respx.mock
def test_eval_raw_javascript_empty(ml):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = ml.eval.javascript(code)

    assert resp == []


@respx.mock
def test_eval_raw_javascript_single_item(ml):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = ml.eval.javascript(code)

    assert resp == ""


@respx.mock
def test_eval_raw_javascript_multiple_items(ml):
    code = "Sequence.from(['', 1]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = ml.eval.javascript(code)

    assert resp == ["", 1]


@respx.mock
def test_eval_js_alias(ml):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = ml.eval.js(code)

    assert resp == []


@respx.mock
def test_eval_variables_explicit(ml):
    code = "declare variable $VARIABLE as xs:string external; $VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": '{"VARIABLE": "X"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, variables={"VARIABLE": "X"})

    assert resp == "X"


@respx.mock
def test_eval_variables_using_kwargs(ml):
    code = "declare variable $VARIABLE as xs:string external; $VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": '{"VARIABLE": "X"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, VARIABLE="X")

    assert resp == "X"


@respx.mock
def test_eval_variables_explicit_with_kwargs(ml):
    code = (
        "declare variable $INTEGER1 external; "
        "declare variable $INTEGER2 external; "
        "$INTEGER1 + $INTEGER2"
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": '{"INTEGER1": 1, "INTEGER2": 2}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "3")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, variables={"INTEGER1": 1}, INTEGER2=2)

    assert resp == 3


@respx.mock
def test_eval_variables_using_namespace(ml):
    code = "declare variable $local:VARIABLE as xs:string external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": f'{{"{{{_LOCAL_NS}}}VARIABLE": "X"}}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, variables={f"{{{_LOCAL_NS}}}VARIABLE": "X"})

    assert resp == "X"


@respx.mock
def test_eval_using_database_param(ml):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, database="Documents")

    assert resp == []


@respx.mock
def test_eval_using_txid_param(ml):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, txid="transaction-id")

    assert resp == []


@respx.mock
def test_eval_file_xquery(ml):
    code = resources_utils.read_test_resource_text(__file__, "xquery-code.xqy")

    ml_mocker = MLRespXMocker(use_router=False)
    for ext in ["xq", "xql", "xqm", "xqu", "xquery", "xqy"]:
        ml_mocker.with_url("http://localhost:8000/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"xquery": code})
        ml_mocker.with_response_code(200)
        ml_mocker.with_empty_response_body()
        ml_mocker.mock_post()

        file_path = resources_utils.get_test_resource_path(
            __file__,
            f"xquery-code.{ext}",
        )
        resp = ml.eval.file(file_path)

        assert resp == []


@respx.mock
def test_eval_file_javascript(ml):
    code = resources_utils.read_test_resource_text(__file__, "javascript-code.js")

    ml_mocker = MLRespXMocker(use_router=False)
    for ext in ["js", "sjs"]:
        ml_mocker.with_url("http://localhost:8000/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"javascript": code})
        ml_mocker.with_response_code(200)
        ml_mocker.with_empty_response_body()
        ml_mocker.mock_post()

        file_path = resources_utils.get_test_resource_path(
            __file__,
            f"javascript-code.{ext}",
        )
        resp = ml.eval.file(file_path)

        assert resp == []


@respx.mock
def test_eval_with_marklogic_error(ml):
    error_body = resources_utils.read_test_resource_bytes(
        __file__,
        "marklogic-error.html",
    )
    code = "declare variable $local:VARIABLE external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("text/html; charset=utf-8")
    ml_mocker.with_response_body(error_body)
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError) as err:
        ml.eval.xquery(code)

    expected_msg = (
        "XDMP-EXTVAR: (err:XPDY0002) "
        "declare variable $local:VARIABLE external;  "
        '-- Undefined external variable xs:QName("local:VARIABLE")\n'
        "in /eval, at 1:43 [1.0-ml]"
    )
    assert err.value.args[0] == expected_msg


def test_eval_execute_rejects_file_with_xquery(ml):
    with pytest.raises(WrongParametersError) as err:
        ml.eval.execute(file="code.xqy", xq="()")

    assert "file" in err.value.args[0]
    assert "xquery" in err.value.args[0]


def test_eval_execute_rejects_file_with_javascript(ml):
    with pytest.raises(WrongParametersError) as err:
        ml.eval.execute(file="code.sjs", js="[];")

    assert "file" in err.value.args[0]
    assert "javascript" in err.value.args[0]


def test_eval_file_unknown_extension(ml):
    with pytest.raises(UnsupportedFileExtensionError) as err:
        ml.eval.file("unknown-extension.txt")

    assert err.value.args[0] == (
        "Unknown file extension! "
        "Supported extensions are: "
        "xq, xql, xqm, xqu, xquery, xqy, js, sjs"
    )


@respx.mock
def test_eval_with_str_output_type(ml):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, output_type=str)

    assert isinstance(resp, str)
    assert resp == "<root/>"


@respx.mock
def test_eval_with_bytes_output_type(ml):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, output_type=bytes)

    assert isinstance(resp, bytes)
    assert resp == b"<root/>"


@pytest.mark.parametrize(
    ("source", "items", "expected"),
    [
        ("()", [], []),
        ("1", [("integer", "text/plain", "1")], 1),
        ("array-node {1, 2}", [("array-node", "application/json", "[1,2]")], [1, 2]),
        (
            "(1, 2)",
            [("integer", "text/plain", "1"), ("integer", "text/plain", "2")],
            [1, 2],
        ),
    ],
)
@respx.mock
def test_eval_collapses_only_the_outer_singleton(source, items, expected):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"xquery": 'xquery version "1.0-ml";\n(' + source + ")"},
    )
    ml_mocker.with_response_code(200)
    for primitive, mime, value in items:
        ml_mocker.with_response_body_part(primitive, value, mime)
    route = ml_mocker.mock_post()
    with MLClient() as ml:
        result = ml.eval.expression(StaticExpression(source))
    assert result == expected
    assert type(result) is type(expected)
    assert route.call_count == 1


class _CountedExpr(XqyExpression):
    def __init__(self):
        self.renders = 0

    def render(self, ctx):
        self.renders += 1
        return xs.decimal(Decimal("1.234567890123456789")).render(ctx)


@respx.mock
def test_wire_parameters_timeout_and_single_compilation():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("decimal", "1.234567890123456789", "text/plain")
    route = ml_mocker.mock_post()
    expr = _CountedExpr()
    with MLClient() as ml:
        assert ml.eval.expression(
            expr,
            database="Documents",
            txid="123",
            timeout=2,
        ) == Decimal("1.234567890123456789")
    request = route.calls.last.request
    body = parse_qs(request.content.decode())
    assert json.loads(body["vars"][0]) == {"v0": "1.234567890123456789"}
    assert body["xquery"] == [
        'xquery version "1.0-ml";\ndeclare variable $v0 as xs:decimal external;\n$v0',
    ]
    assert dict(request.url.params) == {"database": "Documents", "txid": "123"}
    assert request.extensions["timeout"]["read"] == 2
    assert expr.renders == 1


@pytest.mark.parametrize(
    ("expression", "arguments", "error"),
    [
        (xs.string("original"), {"v0": "override"}, TypeError),
        (xs.string("original"), {"variables": {}}, TypeError),
        (xs.string("original"), {"databse": "typo"}, TypeError),
        ("1", {}, TypeError),
        (fn.count([]), {"output_type": int}, ValueError),
    ],
)
@respx.mock
def test_invalid_execution_arguments_fail_before_io(expression, arguments, error):
    with MLClient() as ml, pytest.raises(error):
        ml.eval.expression(expression, **arguments)
    assert not respx.calls


@respx.mock
def test_server_errors_propagate_without_local_version_gates():
    error = {
        "errorResponse": {
            "statusCode": 400,
            "status": "Bad Request",
            "messageCode": "XDMP-UNDFUN",
            "message": "Undefined function cts:document-root-query",
        },
    }
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(error)
    ml_mocker.mock_post()
    expr = cts.document_root_query("x")
    with MLClient() as ml, pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
        ml.eval.expression(expr)


@respx.mock
def test_eval_namespaces_belong_only_to_the_expression_invocation():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "1", "text/plain")
    route = ml_mocker.mock_post()
    with MLClient() as ml:
        ml.eval.expression(
            fn.count([1]),
            namespaces={"p": "https://monasticus.com/mlclient/examples/test"},
        )
        assert (
            'declare namespace p = "https://monasticus.com/mlclient/examples/test";'
            in parse_qs(route.calls.last.request.content.decode())["xquery"][0]
        )
        ml.eval.expression(fn.count([1]))
        assert (
            "declare namespace p"
            not in parse_qs(route.calls.last.request.content.decode())["xquery"][0]
        )


def test_eval_constructor_rejects_namespaces():
    with MLClient() as ml, pytest.raises(TypeError, match="namespaces"):
        type(ml.eval)(
            ml.rest,
            namespaces={"p": "https://monasticus.com/mlclient/examples/test"},
        )
