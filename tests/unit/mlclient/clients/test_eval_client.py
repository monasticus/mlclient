from __future__ import annotations

from pathlib import Path

import pytest
import respx

from mlclient.clients import LOCAL_NS, EvalClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture(autouse=True)
def eval_client() -> EvalClient:
    return EvalClient()


@pytest.fixture(autouse=True)
def _setup_and_teardown(eval_client):
    eval_client.connect()

    yield

    eval_client.disconnect()


@respx.mock
def test_eval_raw_xquery_empty(eval_client):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code)

    assert resp == []


@respx.mock
def test_eval_raw_xquery_single_item(eval_client):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code)

    assert resp == ""


@respx.mock
def test_eval_raw_xquery_multiple_items(eval_client):
    code = "('',1)"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code)

    assert resp == ["", 1]


@respx.mock
def test_eval_raw_javascript_empty(eval_client):
    code = "Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = eval_client.eval(js=code)

    assert resp == []


@respx.mock
def test_eval_raw_javascript_single_item(eval_client):
    code = "''"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.mock_post()

    resp = eval_client.eval(js=code)

    assert resp == ""


@respx.mock
def test_eval_raw_javascript_multiple_items(eval_client):
    code = "Sequence.from(['', 1]);"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"javascript": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "")
    ml_mocker.with_response_body_part("integer", "1")
    ml_mocker.mock_post()

    resp = eval_client.eval(js=code)

    assert resp == ["", 1]


@respx.mock
def test_eval_variables_explicit(eval_client):
    code = "declare variable $VARIABLE as xs:string external; $VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
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

    resp = eval_client.eval(xq=code, variables={"VARIABLE": "X"})

    assert resp == "X"


@respx.mock
def test_eval_variables_using_kwargs(eval_client):
    code = "declare variable $VARIABLE as xs:string external; $VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
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

    resp = eval_client.eval(xq=code, VARIABLE="X")

    assert resp == "X"


@respx.mock
def test_eval_variables_explicit_with_kwargs(eval_client):
    code = (
        "declare variable $INTEGER1 external; "
        "declare variable $INTEGER2 external; "
        "$INTEGER1 + $INTEGER2"
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
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

    resp = eval_client.eval(xq=code, variables={"INTEGER1": 1}, INTEGER2=2)

    assert resp == 3


@respx.mock
def test_eval_variables_using_namespace(eval_client):
    code = "declare variable $local:VARIABLE as xs:string external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": code,
            "vars": f'{{"{{{LOCAL_NS}}}VARIABLE": "X"}}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "X")
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code, variables={f"{{{LOCAL_NS}}}VARIABLE": "X"})

    assert resp == "X"


@respx.mock
def test_eval_using_database_param(eval_client):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code, database="Documents")

    assert resp == []


@respx.mock
def test_eval_using_txid_param(eval_client):
    code = "()"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code, txid="transaction-id")

    assert resp == []


@respx.mock
def test_eval_file_xquery(eval_client):
    code = 'xquery version "1.0-ml"; ()'

    ml_mocker = MLRespXMocker(use_router=False)
    for ext in ["xq", "xql", "xqm", "xqu", "xquery", "xqy"]:
        ml_mocker.with_url("http://localhost:8002/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"xquery": code})
        ml_mocker.with_response_code(200)
        ml_mocker.with_empty_response_body()
        ml_mocker.mock_post()

        file_path = resources_utils.get_test_resource_path(
            __file__,
            f"xquery-code.{ext}",
        )
        resp = eval_client.eval(file=file_path)

        assert resp == []


@respx.mock
def test_eval_file_javascript(eval_client):
    code = "'use strict'; Sequence.from([]);"

    ml_mocker = MLRespXMocker(use_router=False)
    for ext in ["js", "sjs"]:
        ml_mocker.with_url("http://localhost:8002/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"javascript": code})
        ml_mocker.with_response_code(200)
        ml_mocker.with_empty_response_body()
        ml_mocker.mock_post()

        file_path = resources_utils.get_test_resource_path(
            __file__,
            f"javascript-code.{ext}",
        )
        resp = eval_client.eval(file=file_path)

        assert resp == []


@respx.mock
def test_eval_with_marklogic_error(eval_client):
    error_path = resources_utils.get_test_resource_path(
        __file__,
        "marklogic-error.html",
    )
    code = "declare variable $local:VARIABLE external; $local:VARIABLE"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("text/html; charset=utf-8")
    ml_mocker.with_response_body(Path(error_path).read_bytes())
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError) as err:
        eval_client.eval(xq=code)

    expected_msg = (
        "XDMP-EXTVAR: (err:XPDY0002) "
        "declare variable $local:VARIABLE external;  "
        '-- Undefined external variable xs:QName("local:VARIABLE")\n'
        "in /eval, at 1:43 [1.0-ml]"
    )
    assert err.value.args[0] == expected_msg


def test_eval_file_unknown_extension(eval_client):
    with pytest.raises(UnsupportedFileExtensionError) as err:
        eval_client.eval(file="unknown-extension.txt")

    assert err.value.args[0] == (
        "Unknown file extension! "
        "Supported extensions are: "
        "xq, xql, xqm, xqu, xquery, xqy, js, sjs"
    )


def test_eval_mixed_file_and_raw_xquery(eval_client):
    file_path = resources_utils.get_test_resource_path(__file__, "xquery-code.xq")
    with pytest.raises(WrongParametersError) as err:
        eval_client.eval(file=file_path, xq="()")

    expected_msg = "You cannot include both the file and the xquery parameter!"
    assert err.value.args[0] == expected_msg


def test_eval_mixed_file_and_raw_javascript(eval_client):
    file_path = resources_utils.get_test_resource_path(__file__, "javascript-code.js")
    with pytest.raises(WrongParametersError) as err:
        eval_client.eval(file=file_path, js="Sequence.from([]);")

    expected_msg = "You cannot include both the file and the javascript parameter!"
    assert err.value.args[0] == expected_msg


def test_eval_mixed_raw_xquery_and_raw_javascript(eval_client):
    with pytest.raises(WrongParametersError) as err:
        eval_client.eval(xq="()", js="Sequence.from([]);")

    expected_msg = "You cannot include both the xquery and the javascript parameter!"
    assert err.value.args[0] == expected_msg


def test_eval_no_code_params(eval_client):
    with pytest.raises(WrongParametersError) as err:
        eval_client.eval()

    expected_msg = "You must include either the xquery or the javascript parameter!"
    assert err.value.args[0] == expected_msg


@respx.mock
def test_eval_with_str_output_type(eval_client):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code, output_type=str)

    assert isinstance(resp, str)
    assert resp == "<root/>"


@respx.mock
def test_eval_with_bytes_output_type(eval_client):
    code = "element root {}"

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": code})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element", "<root/>")
    ml_mocker.mock_post()

    resp = eval_client.eval(xq=code, output_type=bytes)

    assert isinstance(resp, bytes)
    assert resp == b"<root/>"
