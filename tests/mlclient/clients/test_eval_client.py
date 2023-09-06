from __future__ import annotations

import urllib.parse

import pytest
import responses
from requests_toolbelt import MultipartEncoder

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
    _setup_responses([])

    resp = eval_client.eval(xq="()")

    assert resp == []


@responses.activate
def test_eval_raw_xquery_single_item(eval_client):
    _setup_responses([
        ("string", ""),
    ])

    resp = eval_client.eval(xq="''")

    assert resp == ""


@responses.activate
def test_eval_raw_xquery_multiple_items(eval_client):
    _setup_responses([
        ("string", ""),
        ("integer", "1"),
    ])

    resp = eval_client.eval(xq="('',1)")

    assert resp == ["", 1]


def _setup_responses(
        parts: list[tuple[str, str]],
        request_params: dict | None = None,
):
    request_url = "http://localhost:8002/v1/eval"
    if request_params:
        params = urllib.parse.urlencode(request_params).replace("%2B", "+")
        request_url += f"?{params}"

    if len(parts) == 0:
        responses.post(
            request_url,
            body=b"",
            headers={"Content-Length": "0"},
        )
    else:
        content_type = "text/plain"
        fields = {}
        for i, item in enumerate(parts):
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
        )
