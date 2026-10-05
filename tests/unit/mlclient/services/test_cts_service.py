import inspect
import re
from decimal import Decimal

import pytest
import respx

from mlclient import MLClient
from mlclient.functions.xqy import fn
from mlclient.models import SearchHit, ValueHit
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.services import CtsService
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


METHODS = {
    name: method
    for name, method in CtsService.__dict__.items()
    if not name.startswith("_") and inspect.isfunction(method)
}
REQUESTS = resources_utils.get_test_resource_json(__file__, "requests.json")


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
def test_operation_sends_expected_xquery(case_name, name, variant):
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

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        result = getattr(cts, name)(
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


@respx.mock
def test_pos_range_requires_two_positions():
    with MLClient() as ml:
        cts = CtsService(ml.rest)
        with pytest.raises(
            TypeError, match=re.escape("pos ranges must contain exactly two positions"),
        ) as error:
            cts.search(pos=[1])
    assert str(error.value) == "pos ranges must contain exactly two positions"
    assert not respx.calls


@respx.mock
def test_search_returns_hits_with_scores():
    body, content_type = encode_multipart_mixed(
        [
            MultipartPart(
                {
                    "Content-Type": "application/json",
                    "X-Primitive": "object-node()",
                    "X-URI": "/a.json",
                    "X-Path": "/root",
                },
                b'{"name":"A"}',
            ),
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "integer"},
                b"7",
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
                "for $res in cts:search(/, ())\n"
                "let $measure := cts:score($res)\n"
                "return ($res, $measure)"
            ),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        result = cts.search()

    assert result == [
        SearchHit(
            {"name": "A"},
            score=7,
            source_uri="/a.json",
            source_path="/root",
        ),
    ]


@respx.mock
def test_values_return_hits_with_frequencies():
    body, content_type = encode_multipart_mixed(
        [
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "decimal"},
                b"1.25",
            ),
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "integer"},
                b"2",
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
                "for $res in cts:values(fn:true())\n"
                "let $measure := cts:frequency($res)\n"
                "return ($res, $measure)"
            ),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        result = cts.values(fn.true())

    assert result == [ValueHit(Decimal("1.25"), frequency=2)]


@respx.mock
def test_paired_result_requires_a_measure():
    body, content_type = encode_multipart_mixed(
        [
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "string"},
                b"value",
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
                "for $res in cts:values(fn:true())\n"
                "let $measure := cts:frequency($res)\n"
                "return ($res, $measure)"
            ),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        with pytest.raises(
            ValueError,
            match=re.escape("CTS response is missing a score/frequency partner"),
        ) as error:
            cts.values(fn.true())

    assert str(error.value) == "CTS response is missing a score/frequency partner"


@respx.mock
def test_native_operation_returns_each_response_part():
    body, content_type = encode_multipart_mixed(
        [
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "string"},
                b"/products/a.json",
            ),
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "string"},
                b"/products/b.json",
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
                "cts:uri-match($v0)"
            ),
            "vars": '{"v0": "/products/*.json"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        result = cts.uri_match("/products/*.json")

    assert result == ["/products/a.json", "/products/b.json"]


@respx.mock
def test_native_operation_returns_a_single_response_part():
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

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        result = cts.contains("coffee", cts.word_query("coffee"))

    assert result == [True]


@respx.mock
def test_native_operation_rejects_unsupported_output_type():
    with MLClient() as ml:
        cts = CtsService(ml.rest)
        with pytest.raises(
            ValueError, match=re.escape("output_type must be None, str or bytes"),
        ) as error:
            cts.contains("coffee", cts.word_query("coffee"), output_type=int)
    assert str(error.value) == "output_type must be None, str or bytes"
    assert not respx.calls


@respx.mock
def test_value_operation_rejects_map_in_an_option_sequence():
    with MLClient() as ml:
        cts = CtsService(ml.rest)
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Map output is not a value sequence; use ml.eval.expression(cts...)",
            ),
        ) as error:
            cts.values(fn.true(), options=["item-order", "map"])
    assert (
        str(error.value)
        == "Map output is not a value sequence; use ml.eval.expression(cts...)"
    )
    assert not respx.calls


@respx.mock
def test_value_operation_accepts_a_literal_option_sequence():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "for $res in cts:values(fn:true(), (), ($v0, $v1))\n"
                "let $measure := cts:frequency($res)\n"
                "return ($res, $measure)"
            ),
            "vars": '{"v0": "item-order", "v1": "frequency-order"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as ml:
        cts = CtsService(ml.rest)
        result = cts.values(
            fn.true(),
            options=["item-order", "frequency-order"],
        )

    assert result == []


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
