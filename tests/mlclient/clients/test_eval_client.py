from __future__ import annotations

import urllib.parse

import pytest
import responses
from requests_toolbelt import MultipartEncoder
from responses import matchers

from mlclient.clients import EvalClient


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
