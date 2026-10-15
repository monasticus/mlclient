from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from mlclient.xquery import LOCAL_NS_URI, fn
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


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
            "vars": f'{{"{{{LOCAL_NS_URI}}}VARIABLE": "X"}}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = ml.eval.xquery(code, variables={f"{{{LOCAL_NS_URI}}}VARIABLE": "X"})

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
        resp = ml.eval.file(file_path)

        assert resp == []


@respx.mock
def test_eval_file_javascript(ml):
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

    assert str(err.value) == (
        "You cannot include both the file and the xquery parameter!"
    )


def test_eval_execute_rejects_file_with_javascript(ml):
    with pytest.raises(WrongParametersError) as err:
        ml.eval.execute(file="code.sjs", js="[];")

    assert str(err.value) == (
        "You cannot include both the file and the javascript parameter!"
    )


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


@respx.mock
def test_expression(ml):
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

    result = ml.eval.expression(
        expression,
        namespaces={"p": "https://example.com/test"},
        database="Documents",
        txid="transaction",
        timeout=2,
    )

    assert result == "VALUE"
    assert route.calls.last.request.extensions["timeout"]["read"] == 2


def test_expression_rejects_non_expression(ml):
    with pytest.raises(
        TypeError,
        match=r"^expression requires an XqyExpression$",
    ) as error:
        ml.eval.expression("fn:true()")

    assert str(error.value) == "expression requires an XqyExpression"


def test_expression_rejects_output_type(ml):
    with pytest.raises(
        ValueError,
        match=r"^output_type must be None, str or bytes$",
    ) as error:
        ml.eval.expression(fn.true(), output_type=int)

    assert str(error.value) == "output_type must be None, str or bytes"


@respx.mock
def test_xquery_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.xquery("1")

    assert result == []


@respx.mock
def test_xquery_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.xquery("1", database="request-db", txid="request-tx")

    assert result == []


@respx.mock
def test_xquery_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xquery("1")

    assert result == []


@respx.mock
def test_xquery_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xquery(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_xquery_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xquery(
            "1",
            database=None,
        )

    assert result == []


@respx.mock
def test_xquery_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xquery(
            "1",
            txid=None,
        )

    assert result == []


@respx.mock
def test_xqy_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.xqy("1")

    assert result == []


@respx.mock
def test_xqy_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.xqy("1", database="request-db", txid="request-tx")

    assert result == []


@respx.mock
def test_xqy_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xqy("1")

    assert result == []


@respx.mock
def test_xqy_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xqy(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_xqy_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xqy(
            "1",
            database=None,
        )

    assert result == []


@respx.mock
def test_xqy_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").xqy("1", txid=None)

    assert result == []


@respx.mock
def test_javascript_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.javascript("1")

    assert result == []


@respx.mock
def test_javascript_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.javascript("1", database="request-db", txid="request-tx")

    assert result == []


@respx.mock
def test_javascript_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").javascript("1")

    assert result == []


@respx.mock
def test_javascript_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").javascript(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_javascript_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").javascript(
            "1",
            database=None,
        )

    assert result == []


@respx.mock
def test_javascript_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").javascript(
            "1",
            txid=None,
        )

    assert result == []


@respx.mock
def test_js_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.js("1")

    assert result == []


@respx.mock
def test_js_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.js("1", database="request-db", txid="request-tx")

    assert result == []


@respx.mock
def test_js_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").js("1")

    assert result == []


@respx.mock
def test_js_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").js(
            "1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_js_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").js(
            "1",
            database=None,
        )

    assert result == []


@respx.mock
def test_js_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"javascript": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").js("1", txid=None)

    assert result == []


@respx.mock
def test_file_without_scope(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.file(str(file))

    assert result == []


@respx.mock
def test_file_with_scope_kwargs(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.file(str(file), database="request-db", txid="request-tx")

    assert result == []


@respx.mock
def test_file_inherits_service_scope(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").file(str(file))

    assert result == []


@respx.mock
def test_file_scope_kwargs_override_service_scope(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").file(
            str(file),
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_file_scope_kwargs_clear_service_database(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").file(
            str(file),
            database=None,
        )

    assert result == []


@respx.mock
def test_file_scope_kwargs_clear_service_transaction(tmp_path):
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").file(
            str(file),
            txid=None,
        )

    assert result == []


@respx.mock
def test_execute_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.execute(xq="1")

    assert result == []


@respx.mock
def test_execute_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.execute(xq="1", database="request-db", txid="request-tx")

    assert result == []


@respx.mock
def test_execute_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").execute(xq="1")

    assert result == []


@respx.mock
def test_execute_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").execute(
            xq="1",
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_execute_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").execute(
            xq="1",
            database=None,
        )

    assert result == []


@respx.mock
def test_execute_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").execute(
            xq="1",
            txid=None,
        )

    assert result == []


@respx.mock
def test_expression_without_scope():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.expression(expression)

    assert result == []


@respx.mock
def test_expression_with_scope_kwargs():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval.expression(
            expression,
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_expression_inherits_service_scope():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").expression(
            expression,
        )

    assert result == []


@respx.mock
def test_expression_scope_kwargs_override_service_scope():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").expression(
            expression,
            database="request-db",
            txid="request-tx",
        )

    assert result == []


@respx.mock
def test_expression_scope_kwargs_clear_service_database():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").expression(
            expression,
            database=None,
        )

    assert result == []


@respx.mock
def test_expression_scope_kwargs_clear_service_transaction():
    expression = fn.string_length("coffee")
    (code, variables) = expression.compile()
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": code, "vars": json.dumps(variables)})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "service-db")
    mocker.mock_post()

    with MLClient() as ml:
        result = ml.eval(database="service-db", txid="service-tx").expression(
            expression,
            txid=None,
        )

    assert result == []


@respx.mock
def test_eval_scope_keeps_external_variables_separate():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "$message", "vars": '{"message": "coffee"}'})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.mock_post()

    with MLClient() as ml:
        ml.eval(database="catalog").xquery("$message", message="coffee")


@respx.mock
def test_overriding_scope_on_service_copy_preserves_original_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.mock_post()
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-2")
    mocker.mock_post()

    with MLClient() as ml:
        original_service = ml.eval(database="catalog", txid="tx-1")
        overridden_scope_service = original_service(txid="tx-2")
        overridden_scope_service.xquery("1")
        original_service.xquery("1")


@respx.mock
def test_clearing_scope_on_service_copy_preserves_original_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.mock_post()
    mocker.with_url("http://localhost:8000/v1/eval")
    mocker.with_request_content_type("application/x-www-form-urlencoded")
    mocker.with_request_body({"xquery": "1"})
    mocker.with_response_code(200)
    mocker.with_empty_response_body()
    mocker.mock_post()

    with MLClient() as ml:
        original_service = ml.eval(database="catalog", txid="tx-1")
        cleared_scope_service = original_service(database=None, txid=None)
        cleared_scope_service.xquery("1")
        original_service.xquery("1")
