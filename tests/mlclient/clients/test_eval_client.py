from __future__ import annotations

import urllib.parse

import pytest
import responses
from requests_toolbelt import MultipartEncoder
from responses import matchers

from mlclient.clients import LOCAL_NS, EvalClient
from tests import tools


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
    _setup_responses({"xquery": code}, [])

    resp = eval_client.eval(xq=code)

    assert resp == []


@responses.activate
def test_eval_raw_xquery_single_item(eval_client):
    code = "''"
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[
            ("string", ""),
        ])

    resp = eval_client.eval(xq=code)

    assert resp == ""


@responses.activate
def test_eval_raw_xquery_multiple_items(eval_client):
    code = "('',1)"
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[
            ("string", ""),
            ("integer", "1"),
        ])

    resp = eval_client.eval(xq=code)

    assert resp == ["", 1]


@responses.activate
def test_eval_raw_javascript_empty(eval_client):
    code = "Sequence.from([]);"
    _setup_responses({"javascript": code}, [])

    resp = eval_client.eval(js=code)

    assert resp == []


@responses.activate
def test_eval_raw_javascript_single_item(eval_client):
    code = "''"
    _setup_responses(
        request_body={"javascript": code},
        response_parts=[
            ("string", ""),
        ])

    resp = eval_client.eval(js=code)

    assert resp == ""


@responses.activate
def test_eval_raw_javascript_multiple_items(eval_client):
    code = "Sequence.from(['', 1]);"
    _setup_responses(
        request_body={"javascript": code},
        response_parts=[
            ("string", ""),
            ("integer", "1"),
        ])

    resp = eval_client.eval(js=code)

    assert resp == ["", 1]


@responses.activate
def test_eval_variables_explicit(eval_client):
    code = ("declare variable $VARIABLE external; "
            "$VARIABLE")
    _setup_responses(
        request_body={"xquery": code, "vars": '{"VARIABLE": "X"}'},
        response_parts=[
            ("string", "X"),
        ])

    resp = eval_client.eval(xq=code, variables={"VARIABLE": "X"})

    assert resp == "X"


@responses.activate
def test_eval_variables_using_kwargs(eval_client):
    code = ("declare variable $VARIABLE external; "
            "$VARIABLE")
    _setup_responses(
        request_body={"xquery": code, "vars": '{"VARIABLE": "X"}'},
        response_parts=[
            ("string", "X"),
        ])

    resp = eval_client.eval(xq=code, VARIABLE="X")

    assert resp == "X"


@responses.activate
def test_eval_variables_explicit_with_kwargs(eval_client):
    code = ("declare variable $INTEGER1 external; "
            "declare variable $INTEGER2 external; "
            "$INTEGER1 + $INTEGER2")
    _setup_responses(
        request_body={"xquery": code, "vars": '{"INTEGER1": 1, "INTEGER2": 2}'},
        response_parts=[
            ("integer", "3"),
        ])

    resp = eval_client.eval(xq=code, variables={"INTEGER1": 1}, INTEGER2=2)

    assert resp == 3


@responses.activate
def test_eval_variables_using_namespace(eval_client):
    code = ("declare variable $local:VARIABLE external; "
            "$local:VARIABLE")
    _setup_responses(
        request_body={"xquery": code, "vars": f'{{"{{{LOCAL_NS}}}VARIABLE": "X"}}'},
        response_parts=[
            ("string", "X"),
        ])

    resp = eval_client.eval(xq=code, variables={f"{{{LOCAL_NS}}}VARIABLE": "X"})

    assert resp == "X"


@responses.activate
def test_eval_using_database_param(eval_client):
    code = "()"
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[],
        request_params={"database": "Documents"})

    resp = eval_client.eval(xq=code, database="Documents")

    assert resp == []


@responses.activate
def test_eval_using_txid_param(eval_client):
    code = "()"
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[],
        request_params={"txid": "transaction-id"})

    resp = eval_client.eval(xq=code, txid="transaction-id")

    assert resp == []


@responses.activate
def test_eval_xquery_file(eval_client):
    code = 'xquery version "1.0-ml"; ()'

    for ext in ["xq", "xql", "xqm", "xqu", "xquery", "xqy"]:
        _setup_responses(
            request_body={"xquery": code},
            response_parts=[])

        file_path = tools.get_test_resource_path(__file__, f"xquery-code.{ext}")
        resp = eval_client.eval(file=file_path)

        assert resp == []


@responses.activate
def test_eval_javascript_file(eval_client):
    code = "'use strict'; Sequence.from([]);"

    for ext in ["js", "sjs"]:
        _setup_responses(
            request_body={"javascript": code},
            response_parts=[])

        file_path = tools.get_test_resource_path(__file__, f"javascript-code.{ext}")
        resp = eval_client.eval(file=file_path)

        assert resp == []


def _setup_responses(
        request_body: dict,
        response_parts: list[tuple[str, str]],
        request_params: dict | None = None,
):
    request_url = "http://localhost:8002/v1/eval"
    if request_params:
        params = urllib.parse.urlencode(request_params).replace("%2B", "+")
        request_url += f"?{params}"

    if len(response_parts) == 0:
        responses.post(
            request_url,
            body=b"",
            headers={"Content-Length": "0"},
            match=[matchers.urlencoded_params_matcher(request_body)],
        )
    else:
        content_type = "text/plain"
        fields = {}
        for i, item in enumerate(response_parts):
            name_disposition = f"name{i}"
            field_name = f"field{i}"
            field_value = item[1]
            x_primitive = item[0]
            headers = {"X-Primitive": x_primitive}
            fields[field_name] = (name_disposition, field_value, content_type, headers)
        multipart_body = MultipartEncoder(fields=fields)
        multipart_body_str = multipart_body.to_string()
        responses.post(
            request_url,
            body=multipart_body_str,
            content_type=f"multipart/mixed; boundary={multipart_body.boundary[2:]}",
            headers={
                "Content-Length": str(len(multipart_body_str)),
            },
            match=[matchers.urlencoded_params_matcher(request_body)],
        )
