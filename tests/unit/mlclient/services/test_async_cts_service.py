import inspect
import re
from pathlib import Path

import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.xquery import fn
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.services import AsyncCtsService
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


METHODS = {
    name: method
    for name, method in AsyncCtsService.__dict__.items()
    if not name.startswith("_") and inspect.iscoroutinefunction(method)
}
SYNC_TEST = Path(__file__).with_name("test_cts_service.py").as_posix()
REQUESTS = resources_utils.get_test_resource_json(SYNC_TEST, "requests.json")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case_name", "name", "variant"),
    [
        (case_name, case_name.removesuffix(f"-{variant}"), variant)
        for case_name in REQUESTS
        for variant in ("range-literal", "range-expr", "index", "all")
        if case_name.endswith(f"-{variant}")
    ],
    ids=lambda value: value,
)
@respx.mock
async def test_operation_sends_expected_xquery(case_name, name, variant):
    expected = REQUESTS[case_name]
    pos = (
        {
            "range-literal": [1, 2],
            "range-expr": (1, fn.last()),
            "index": 2,
        }[variant]
        if "pos" in inspect.signature(METHODS[name]).parameters
        else None
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_header(
        "Content-Type",
        "application/x-www-form-urlencoded",
    )
    for key, value in expected["params"].items():
        ml_mocker.with_request_param(key, value)
    ml_mocker.with_request_body(expected["body"])
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        result = await getattr(cts, name)(
            **_arguments(METHODS[name], pos),
            database="Documents",
            txid="transaction",
            timeout=2,
            namespaces={
                "t": "https://monasticus.com/mlclient/examples/cts-test",
            },
        )

    assert result == []
    assert route.call_count == 1
    assert route.calls.last.request.extensions["timeout"]["read"] == 2


@pytest.mark.asyncio
@respx.mock
async def test_pos_range_requires_two_positions():
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        with pytest.raises(
            TypeError, match=re.escape("pos ranges must contain exactly two positions"),
        ) as error:
            await cts.search(pos=[1])
    assert str(error.value) == "pos ranges must contain exactly two positions"
    assert not respx.calls


@pytest.mark.asyncio
@respx.mock
async def test_native_operation_returns_response_parts():
    body, content_type = encode_multipart_mixed(
        [
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "boolean"},
                b"true",
            ),
        ],
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "cts:contains($v0, cts:word-query($v1))"
            ),
            "vars": '{"v0": "coffee", "v1": "coffee"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        result = await cts.contains("coffee", cts.word_query("coffee"))

    assert result == [True]


@pytest.mark.asyncio
@respx.mock
async def test_native_operation_rejects_unsupported_output_type():
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        with pytest.raises(
            ValueError, match=re.escape("output_type must be None, str or bytes"),
        ) as error:
            await cts.contains(
                "coffee",
                cts.word_query("coffee"),
                output_type=int,
            )
    assert str(error.value) == "output_type must be None, str or bytes"
    assert not respx.calls


def _arguments(method, pos):
    arguments = {}
    for name, parameter in inspect.signature(method).parameters.items():
        if name == "self" or parameter.kind is inspect.Parameter.VAR_KEYWORD:
            continue
        if name == "pos":
            arguments[name] = pos
        elif name == "xpath":
            arguments[name] = "t:child"
        else:
            arguments[name] = fn.true()
    return arguments
