from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from mlclient.functions.xqy import XqyExpression, cts, fn, xs
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.responses import MLResponseParser
from mlclient.services.eval import _LOCAL_NS
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest.mark.parametrize("body", [b"", b"<html>Unavailable</html>"])
@respx.mock
def test_expression_preserves_unrecognized_http_errors(ml, body):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(503, content=body),
    )
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
    route = respx.post(
        "http://localhost:8000/v1/eval",
        data={"xquery": "1"},
    ).respond(403)

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
    code = Path(
        resources_utils.get_test_resource_path(__file__, "xquery-code.xqy"),
    ).read_text()

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
    code = Path(
        resources_utils.get_test_resource_path(__file__, "javascript-code.js"),
    ).read_text()

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
    error_path = resources_utils.get_test_resource_path(
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
    ml_mocker.with_response_body(Path(error_path).read_bytes())
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


def _response(*items):
    parts = [
        MultipartPart({"Content-Type": mime, "X-Primitive": primitive}, value.encode())
        for primitive, mime, value in items
    ]
    body, content_type = encode_multipart_mixed(parts)
    return httpx.Response(200, content=body, headers={"Content-Type": content_type})


@pytest.mark.parametrize(
    ("items", "expected"),
    [
        ([], []),
        ([("integer", "text/plain", "0")], 0),
        ([("boolean", "text/plain", "false")], False),
        ([("string", "text/plain", "")], ""),
        ([("array-node", "application/json", "[]")], []),
        ([("array-node", "application/json", "[1,2]")], [1, 2]),
        ([("array-node", "application/json", "[[1]]")], [[1]]),
        (
            [("integer", "text/plain", "1"), ("integer", "text/plain", "2")],
            [1, 2],
        ),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_eval_collapses_only_the_outer_singleton(items, expected):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(*items),
    )
    with MLClient() as ml:
        result = ml.eval.expression(fn.count([]))
    async with AsyncMLClient() as ml:
        async_result = await ml.eval.expression(fn.count([]))
    assert result == expected
    assert type(result) is type(expected)
    assert async_result == expected
    assert type(async_result) is type(expected)
    assert route.call_count == 2


@respx.mock
def test_typed_items_and_raw_overrides_share_parser():
    items = [
        ("decimal", "text/plain", "1.234567890123456789"),
        ("double", "text/plain", "1.25"),
        ("float", "text/plain", "INF"),
        ("unsignedLong", "text/plain", "18446744073709551615"),
        ("date", "text/plain", "2026-01-02"),
        ("dateTime", "text/plain", "2026-01-02T03:04:05Z"),
        ("dateTime", "text/plain", "2026-01-02T03:04:05.123"),
        ("boolean", "text/plain", "1"),
        ("boolean", "text/plain", "false"),
        ("QName", "text/plain", "p:x"),
    ]
    respx.post("http://localhost:8000/v1/eval").mock(return_value=_response(*items))
    with MLClient() as ml:
        assert ml.eval.expression(xs.string("unused")) == [
            Decimal("1.234567890123456789"),
            1.25,
            float("inf"),
            18446744073709551615,
            date(2026, 1, 2),
            datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            datetime(2026, 1, 2, 3, 4, 5, 123000),
            True,
            False,
            b"p:x",
        ]
        assert ml.eval.expression(fn.count([]), output_type=str) == [
            i[2] for i in items
        ]
        assert ml.eval.expression(fn.count([]), output_type=bytes) == [
            i[2].encode() for i in items
        ]
    response = _response(items[0])
    response.request = httpx.Request("POST", "http://localhost/v1/eval")
    assert MLResponseParser.parse(response) == Decimal(items[0][2])


@respx.mock
def test_xml_json_and_nonmultipart_results():
    route = respx.post("http://localhost:8000/v1/eval")
    with MLClient() as ml:
        route.mock(
            return_value=_response(
                ("document-node()", "application/xml", "<a/>"),
                ("element", "application/xml", "<b/>"),
                ("object-node", "application/json", '{"a":1}'),
            ),
        )
        a, b, c = ml.eval.expression(cts.search())
        assert a.getroot().tag == "a"
        assert b.tag == "b"
        assert c == {"a": 1}
        route.mock(
            return_value=httpx.Response(
                200,
                content="7",
                headers={"Content-Type": "text/plain", "X-Primitive": "integer"},
            ),
        )
        assert ml.eval.expression(fn.count([])) == 7
        route.mock(return_value=httpx.Response(200, content=b""))
        assert ml.eval.expression(fn.count([])) == []


class _CountedExpr(XqyExpression):
    def __init__(self):
        self.renders = 0

    def render(self, ctx):
        self.renders += 1
        return xs.decimal(Decimal("1.234567890123456789")).render(ctx)


@respx.mock
def test_wire_parameters_timeout_and_single_compilation():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("decimal", "text/plain", "1.234567890123456789")),
    )
    expr = _CountedExpr()
    with MLClient() as ml:
        assert ml.eval.expression(
            expr,
            database="test",
            txid="123",
            timeout=2,
        ) == Decimal("1.234567890123456789")
    request = route.calls.last.request
    body = parse_qs(request.content.decode())
    assert json.loads(body["vars"][0]) == {"v0": "1.234567890123456789"}
    assert "\n" in body["xquery"][0]
    assert dict(request.url.params) == {"database": "test", "txid": "123"}
    assert request.extensions["timeout"]["read"] == 2
    assert expr.renders == 1


@pytest.mark.asyncio
@respx.mock
async def test_invalid_execution_arguments_fail_before_io_sync_and_async():
    with MLClient() as ml:
        for kwargs in ({"v0": "override"}, {"variables": {}}, {"databse": "typo"}):
            with pytest.raises(TypeError):
                ml.eval.expression(xs.string("original"), **kwargs)
        with pytest.raises(TypeError, match="XqyExpression"):
            ml.eval.expression("1")
        with pytest.raises(ValueError, match="output_type"):
            ml.eval.expression(fn.count([]), output_type=int)
    async with AsyncMLClient() as ml:
        with pytest.raises(TypeError, match="XqyExpression"):
            await ml.eval.expression("1")
        with pytest.raises(ValueError, match="output_type"):
            await ml.eval.expression(fn.count([]), output_type=int)
        with pytest.raises(TypeError):
            await ml.eval.expression(fn.count([]), v0="override")
    assert not respx.calls


@pytest.mark.asyncio
@respx.mock
async def test_server_errors_propagate_without_local_version_gates():
    error = {
        "errorResponse": {
            "statusCode": 400,
            "status": "Bad Request",
            "messageCode": "XDMP-UNDFUN",
            "message": "Undefined function cts:document-root-query",
        },
    }
    respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(400, json=error["errorResponse"]),
    )
    expr = cts.document_root_query("x")
    with MLClient() as ml, pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
        ml.eval.expression(expr)
    async with AsyncMLClient() as ml:
        with pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
            await ml.eval.expression(expr)


@pytest.mark.asyncio
@respx.mock
async def test_eval_namespaces_belong_only_to_the_expression_invocation():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("integer", "text/plain", "1")),
    )
    with MLClient() as ml:
        ml.eval.expression(fn.count([1]), namespaces={"p": "urn:test"})
        assert (
            'declare namespace p = "urn:test";'
            in parse_qs(
                route.calls.last.request.content.decode(),
            )["xquery"][0]
        )
        ml.eval.expression(fn.count([1]))
        assert (
            "declare namespace p"
            not in parse_qs(
                route.calls.last.request.content.decode(),
            )["xquery"][0]
        )
        with pytest.raises(TypeError, match="namespaces"):
            type(ml.eval)(ml.rest, namespaces={"p": "urn:test"})
    async with AsyncMLClient() as ml:
        await ml.eval.expression(fn.count([1]), namespaces={"p": "urn:test"})
        assert (
            'declare namespace p = "urn:test";'
            in parse_qs(
                route.calls.last.request.content.decode(),
            )["xquery"][0]
        )
        await ml.eval.expression(fn.count([1]))
        assert (
            "declare namespace p"
            not in parse_qs(
                route.calls.last.request.content.decode(),
            )["xquery"][0]
        )
        with pytest.raises(TypeError, match="namespaces"):
            type(ml.eval)(ml.rest, namespaces={"p": "urn:test"})
