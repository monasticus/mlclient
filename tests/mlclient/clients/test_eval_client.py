from __future__ import annotations

from pathlib import Path

import pytest
import responses

from mlclient.clients import LOCAL_NS, EvalClient
from mlclient.exceptions import (MarkLogicError, UnsupportedFileExtensionError,
                                 WrongParametersError)
from tests import tools
from tests.tools import MLResponseBuilder


@pytest.fixture(autouse=True)
def eval_client() -> EvalClient:
    return EvalClient()


@pytest.fixture(autouse=True)
def _setup_and_teardown(eval_client):
    eval_client.connect()

    yield

    eval_client.disconnect()


@responses.activate
def test_eval_raw_xquery_empty(eval_client):
    code = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_empty_response_body()
    builder.build_post()

    resp = eval_client.eval(xq=code)

    assert resp == []


@responses.activate
def test_eval_raw_xquery_single_item(eval_client):
    code = "''"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_part("string", "")
    builder.build_post()

    resp = eval_client.eval(xq=code)

    assert resp == ""


@responses.activate
def test_eval_raw_xquery_multiple_items(eval_client):
    code = "('',1)"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_part("string", "")
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = eval_client.eval(xq=code)

    assert resp == ["", 1]


@responses.activate
def test_eval_raw_javascript_empty(eval_client):
    code = "Sequence.from([]);"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"javascript": code})
    builder.with_empty_response_body()
    builder.build_post()

    resp = eval_client.eval(js=code)

    assert resp == []


@responses.activate
def test_eval_raw_javascript_single_item(eval_client):
    code = "''"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"javascript": code})
    builder.with_response_body_part("string", "")
    builder.build_post()

    resp = eval_client.eval(js=code)

    assert resp == ""


@responses.activate
def test_eval_raw_javascript_multiple_items(eval_client):
    code = "Sequence.from(['', 1]);"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"javascript": code})
    builder.with_response_body_part("string", "")
    builder.with_response_body_part("integer", "1")
    builder.build_post()

    resp = eval_client.eval(js=code)

    assert resp == ["", 1]


@responses.activate
def test_eval_variables_explicit(eval_client):
    code = ("declare variable $VARIABLE external; "
            "$VARIABLE")

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({
        "xquery": code,
        "vars": '{"VARIABLE": "X"}',
    })
    builder.with_response_body_part("string", "X")
    builder.build_post()

    resp = eval_client.eval(xq=code, variables={"VARIABLE": "X"})

    assert resp == "X"


@responses.activate
def test_eval_variables_using_kwargs(eval_client):
    code = ("declare variable $VARIABLE external; "
            "$VARIABLE")

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({
        "xquery": code,
        "vars": '{"VARIABLE": "X"}',
    })
    builder.with_response_body_part("string", "X")
    builder.build_post()

    resp = eval_client.eval(xq=code, VARIABLE="X")

    assert resp == "X"


@responses.activate
def test_eval_variables_explicit_with_kwargs(eval_client):
    code = ("declare variable $INTEGER1 external; "
            "declare variable $INTEGER2 external; "
            "$INTEGER1 + $INTEGER2")

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({
        "xquery": code,
        "vars": '{"INTEGER1": 1, "INTEGER2": 2}',
    })
    builder.with_response_body_part("integer", "3")
    builder.build_post()

    resp = eval_client.eval(xq=code, variables={"INTEGER1": 1}, INTEGER2=2)

    assert resp == 3


@responses.activate
def test_eval_variables_using_namespace(eval_client):
    code = ("declare variable $local:VARIABLE external; "
            "$local:VARIABLE")

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({
        "xquery": code,
        "vars": f'{{"{{{LOCAL_NS}}}VARIABLE": "X"}}',
    })
    builder.with_response_body_part("string", "X")
    builder.build_post()

    resp = eval_client.eval(xq=code, variables={f"{{{LOCAL_NS}}}VARIABLE": "X"})

    assert resp == "X"


@responses.activate
def test_eval_using_database_param(eval_client):
    code = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_param("database", "Documents")
    builder.with_request_body({"xquery": code})
    builder.with_empty_response_body()
    builder.build_post()

    resp = eval_client.eval(xq=code, database="Documents")

    assert resp == []


@responses.activate
def test_eval_using_txid_param(eval_client):
    code = "()"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_param("txid", "transaction-id")
    builder.with_request_body({"xquery": code})
    builder.with_empty_response_body()
    builder.build_post()

    resp = eval_client.eval(xq=code, txid="transaction-id")

    assert resp == []


@responses.activate
def test_eval_file_xquery(eval_client):
    code = 'xquery version "1.0-ml"; ()'

    builder = MLResponseBuilder()
    for ext in ["xq", "xql", "xqm", "xqu", "xquery", "xqy"]:
        builder.with_base_url("http://localhost:8002/v1/eval")
        builder.with_request_body({"xquery": code})
        builder.with_empty_response_body()
        builder.build_post()

        file_path = tools.get_test_resource_path(__file__, f"xquery-code.{ext}")
        resp = eval_client.eval(file=file_path)

        assert resp == []


@responses.activate
def test_eval_file_javascript(eval_client):
    code = "'use strict'; Sequence.from([]);"

    builder = MLResponseBuilder()
    for ext in ["js", "sjs"]:
        builder.with_base_url("http://localhost:8002/v1/eval")
        builder.with_request_body({"javascript": code})
        builder.with_empty_response_body()
        builder.build_post()

        file_path = tools.get_test_resource_path(__file__, f"javascript-code.{ext}")
        resp = eval_client.eval(file=file_path)

        assert resp == []


@responses.activate
def test_eval_with_marklogic_error(eval_client):
    error_path = tools.get_test_resource_path(__file__, "marklogic-error.html")
    code = ("declare variable $local:VARIABLE external; "
            "$local:VARIABLE")

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_status(400)
    builder.with_response_body(Path(error_path).read_bytes())
    builder.build_post()

    with pytest.raises(MarkLogicError) as err:
        eval_client.eval(xq=code)

    expected_msg = ('XDMP-EXTVAR: (err:XPDY0002) '
                    'declare variable $local:VARIABLE external;  '
                    '-- Undefined external variable xs:QName("local:VARIABLE")\n'
                    'in /eval, at 1:43 [1.0-ml]')
    assert err.value.args[0] == expected_msg


def test_eval_file_unknown_extension(eval_client):
    with pytest.raises(UnsupportedFileExtensionError) as err:
        eval_client.eval(file="unknown-extension.txt")

    assert err.value.args[0] == ("Unknown file extension! "
                                 "Supported extensions are: "
                                 "xq, xql, xqm, xqu, xquery, xqy, js, sjs")


def test_eval_mixed_file_and_raw_xquery(eval_client):
    file_path = tools.get_test_resource_path(__file__, "xquery-code.xq")
    with pytest.raises(WrongParametersError) as err:
        eval_client.eval(file=file_path, xq="()")

    expected_msg = "You cannot include both the file and the xquery parameter!"
    assert err.value.args[0] == expected_msg


def test_eval_mixed_file_and_raw_javascript(eval_client):
    file_path = tools.get_test_resource_path(__file__, "javascript-code.js")
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


@responses.activate
def test_eval_with_raw_flag(eval_client):
    code = "element root {}"

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_part("element", "<root/>")
    builder.build_post()

    resp = eval_client.eval(xq=code, raw=True)

    assert isinstance(resp, str)
    assert resp == "<root/>"
