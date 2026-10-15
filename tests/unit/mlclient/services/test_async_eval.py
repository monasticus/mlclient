from __future__ import annotations

import json

import httpx
import pytest
import pytest_asyncio
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from mlclient.xquery import LOCAL_NS_URI, fn
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest_asyncio.fixture
async def svc():

    async with AsyncMLClient() as ml:
        yield ml.eval


@pytest.mark.asyncio
@respx.mock
async def test_eval_preserves_bodyless_http_failure(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": "1"})
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    with pytest.raises(httpx.HTTPStatusError) as raised:
        await svc.xquery("1")

    assert route.call_count == 1
    assert raised.value.response.url == route.calls.last.request.url
    assert raised.value.response.status_code == 403


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_xquery_empty(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xquery(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_timeout_reaches_transport_and_is_not_a_query_variable(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    await svc.xquery(code, timeout=2)

    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_eval_variable_named_timeout_is_sent_as_query_variable(svc):
    code = "declare variable $timeout external; $timeout"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code, "vars": '{"timeout": 30}'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "30")
    route = ml_mocker.mock_post()

    resp = await svc.xquery(code, variables={"timeout": 30}, timeout=2)

    assert resp == 30
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_xquery_single_item(svc):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = await svc.xquery(code)

    assert resp == ""


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_xquery_multiple_items(svc):
    code = "('',1)"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = await svc.xquery(code)

    assert resp == ["", 1]


@pytest.mark.asyncio
@respx.mock
async def test_eval_xqy_alias(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xqy(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_javascript_empty(svc):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.javascript(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_javascript_single_item(svc):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = await svc.javascript(code)

    assert resp == ""


@pytest.mark.asyncio
@respx.mock
async def test_eval_raw_javascript_multiple_items(svc):
    code = "Sequence.from(['', 1]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = await svc.javascript(code)

    assert resp == ["", 1]


@pytest.mark.asyncio
@respx.mock
async def test_eval_js_alias(svc):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.js(code)

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_explicit(svc):
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

    resp = await svc.xquery(code, variables={"VARIABLE": "X"})

    assert resp == "X"


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_using_kwargs(svc):
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

    resp = await svc.xquery(code, VARIABLE="X")

    assert resp == "X"


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_explicit_with_kwargs(svc):
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

    resp = await svc.xquery(code, variables={"INTEGER1": 1}, INTEGER2=2)

    assert resp == 3


@pytest.mark.asyncio
@respx.mock
async def test_eval_variables_using_namespace(svc):
    code = "declare variable $local:VARIABLE as xs:string external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": f'{{"{{{LOCAL_NS_URI}}}VARIABLE": "X"}}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, variables={f"{{{LOCAL_NS_URI}}}VARIABLE": "X"})

    assert resp == "X"


@pytest.mark.asyncio
@respx.mock
async def test_eval_using_database_param(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xquery(code, database="Documents")

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_using_txid_param(svc):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = await svc.xquery(code, txid="transaction-id")

    assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_file_xquery(svc):
    code = 'xquery version "1.0-ml";\n\n()\n'

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
        resp = await svc.file(file_path)

        assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_file_javascript(svc):
    code = "'use strict';\n\nSequence.from([]);\n"

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
        resp = await svc.file(file_path)

        assert resp == []


@pytest.mark.asyncio
@respx.mock
async def test_eval_with_marklogic_error(svc):
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
        await svc.xquery(code)

    expected_msg = (
        "XDMP-EXTVAR: (err:XPDY0002) "
        "declare variable $local:VARIABLE external;  "
        '-- Undefined external variable xs:QName("local:VARIABLE")\n'
        "in /eval, at 1:43 [1.0-ml]"
    )
    assert err.value.args[0] == expected_msg


@pytest.mark.asyncio
async def test_eval_execute_rejects_file_with_xquery(svc):
    with pytest.raises(WrongParametersError) as err:
        await svc.execute(file="code.xqy", xq="()")

    assert str(err.value) == (
        "You cannot include both the file and the xquery parameter!"
    )


@pytest.mark.asyncio
async def test_eval_execute_rejects_file_with_javascript(svc):
    with pytest.raises(WrongParametersError) as err:
        await svc.execute(file="code.sjs", js="[];")

    assert str(err.value) == (
        "You cannot include both the file and the javascript parameter!"
    )


@pytest.mark.asyncio
async def test_eval_file_unknown_extension(svc):
    with pytest.raises(UnsupportedFileExtensionError) as err:
        await svc.file("unknown-extension.txt")

    assert err.value.args[0] == (
        "Unknown file extension! "
        "Supported extensions are: "
        "xq, xql, xqm, xqu, xquery, xqy, js, sjs"
    )


@pytest.mark.asyncio
@respx.mock
async def test_eval_with_str_output_type(svc):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, output_type=str)

    assert isinstance(resp, str)
    assert resp == "<root/>"


@pytest.mark.asyncio
@respx.mock
async def test_eval_with_bytes_output_type(svc):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = await svc.xquery(code, output_type=bytes)

    assert isinstance(resp, bytes)
    assert resp == b"<root/>"


@pytest.mark.asyncio
@respx.mock
async def test_expression(svc):
    expression = fn.upper_case("value")
    code, variables = expression.compile(namespaces={"p": "https://example.com/test"})
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("txid", "transaction")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "VALUE")
    route = ml_mocker.mock_post()

    result = await svc.expression(
        expression,
        namespaces={"p": "https://example.com/test"},
        database="Documents",
        txid="transaction",
        timeout=2,
    )

    assert result == "VALUE"
    assert route.calls.last.request.extensions["timeout"]["read"] == 2


@pytest.mark.asyncio
async def test_expression_rejects_non_expression(svc):
    with pytest.raises(
        TypeError,
        match=r"^expression requires an XqyExpression$",
    ) as error:
        await svc.expression("fn:true()")

    assert str(error.value) == "expression requires an XqyExpression"


@pytest.mark.asyncio
async def test_expression_rejects_output_type(svc):
    with pytest.raises(
        ValueError,
        match=r"^output_type must be None, str or bytes$",
    ) as error:
        await svc.expression(fn.true(), output_type=int)

    assert str(error.value) == "output_type must be None, str or bytes"


@pytest.mark.asyncio
@respx.mock
async def test_xquery_unscoped():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.xquery("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xquery_keywords():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.xquery("1", database="request-db", txid="request-tx")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xquery_service_scope():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xquery("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xquery_override_service():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xquery(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xquery_clear_database():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xquery(
            "1",
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xquery_clear_transaction():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xquery(
            "1",
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xqy_unscoped():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.xqy("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xqy_keywords():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.xqy("1", database="request-db", txid="request-tx")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xqy_service_scope():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xqy("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xqy_override_service():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xqy(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xqy_clear_database():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xqy(
            "1",
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_xqy_clear_transaction():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").xqy(
            "1",
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_javascript_unscoped():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.javascript("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_javascript_keywords():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.javascript(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_javascript_service_scope():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").javascript("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_javascript_override_service():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").javascript(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_javascript_clear_database():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").javascript(
            "1",
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_javascript_clear_transaction():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").javascript(
            "1",
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_js_unscoped():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.js("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_js_keywords():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.js("1", database="request-db", txid="request-tx")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_js_service_scope():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").js("1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_js_override_service():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").js(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_js_clear_database():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").js(
            "1",
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_js_clear_transaction():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").js(
            "1",
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_file_unscoped(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.file(str(file))

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_file_keywords(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.file(
            str(file),
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_file_service_scope(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").file(str(file))

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_file_override_service(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").file(
            str(file),
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_file_clear_database(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").file(
            str(file),
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_file_clear_transaction(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").file(
            str(file),
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_execute_unscoped():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.execute(xq="1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_execute_keywords():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.execute(
            xq="1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_execute_service_scope():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").execute(xq="1")

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_execute_override_service():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").execute(
            xq="1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_execute_clear_database():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").execute(
            xq="1",
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_execute_clear_transaction():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").execute(
            xq="1",
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_expression_unscoped():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.expression(expression)

    assert result == []
    assert dict(route.calls.last.request.url.params) == {}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_expression_keywords():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval.expression(
            expression,
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_expression_service_scope():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").expression(
            expression,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "service-db",
        "txid": "service-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_expression_override_service():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").expression(
            expression,
            database="request-db",
            txid="request-tx",
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {
        "database": "request-db",
        "txid": "request-tx",
    }
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_expression_clear_database():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").expression(
            expression,
            database=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"txid": "service-tx"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_expression_clear_transaction():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.eval(database="service-db", txid="service-tx").expression(
            expression,
            txid=None,
        )

    assert result == []
    assert dict(route.calls.last.request.url.params) == {"database": "service-db"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_scoped_service_narrow_preserves_original():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    original_route = mocker.mock_post()
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-2")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    changed_route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        original = ml.eval(database="catalog", txid="tx-1")
        changed = original(txid="tx-2")
        assert changed_route.call_count == 0
        assert original_route.call_count == 0
        await changed.xquery("1")
        await original.xquery("1")

    assert dict(changed_route.calls.last.request.url.params) == {
        "database": "catalog",
        "txid": "tx-2",
    }
    assert dict(original_route.calls.last.request.url.params) == {
        "database": "catalog",
        "txid": "tx-1",
    }
    assert changed_route.call_count == 1
    assert original_route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_scoped_service_clear_preserves_original():
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    original_route = mocker.mock_post()
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    changed_route = mocker.mock_post()

    async with AsyncMLClient() as ml:
        original = ml.eval(database="catalog", txid="tx-1")
        changed = original(database=None, txid=None)
        assert changed_route.call_count == 0
        assert original_route.call_count == 0
        await changed.xquery("1")
        await original.xquery("1")

    assert dict(changed_route.calls.last.request.url.params) == {}
    assert dict(original_route.calls.last.request.url.params) == {
        "database": "catalog",
        "txid": "tx-1",
    }
    assert changed_route.call_count == 1
    assert original_route.call_count == 1
