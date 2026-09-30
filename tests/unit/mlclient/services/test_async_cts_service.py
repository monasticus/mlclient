from __future__ import annotations

import inspect
import json
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError
from mlclient.functions.xqy import fn, xs
from mlclient.models import SearchHit, ValueHit
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.services import AsyncCtsService
from tests.utils.expressions import StaticExpression
from tests.utils.ml_mockers import MLRespXMocker


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        "aggregate",
        "avg_aggregate",
        "classify",
        "cluster",
        "collection_match",
        "collections",
        "confidence",
        "contains",
        "correlation",
        "count_aggregate",
        "covariance",
        "covariance_p",
        "deregister",
        "distinctive_terms",
        "element_attribute_pair_geospatial_boxes",
        "element_attribute_pair_geospatial_value_match",
        "element_attribute_pair_geospatial_values",
        "element_attribute_value_co_occurrences",
        "element_attribute_value_geospatial_co_occurrences",
        "element_attribute_value_match",
        "element_attribute_value_ranges",
        "element_attribute_values",
        "element_attribute_word_match",
        "element_attribute_words",
        "element_child_geospatial_boxes",
        "element_child_geospatial_value_match",
        "element_child_geospatial_values",
        "element_geospatial_boxes",
        "element_geospatial_value_match",
        "element_geospatial_values",
        "element_pair_geospatial_boxes",
        "element_pair_geospatial_value_match",
        "element_pair_geospatial_values",
        "element_value_co_occurrences",
        "element_value_geospatial_co_occurrences",
        "element_value_match",
        "element_value_ranges",
        "element_values",
        "element_walk",
        "element_word_match",
        "element_words",
        "entity_dictionary_get",
        "entity_highlight",
        "entity_walk",
        "field_value_co_occurrences",
        "field_value_match",
        "field_value_ranges",
        "field_values",
        "field_word_match",
        "field_words",
        "fitness",
        "frequency",
        "geospatial_boxes",
        "geospatial_co_occurrences",
        "highlight",
        "json_property_word_match",
        "json_property_words",
        "linear_model",
        "match_regions",
        "max",
        "median",
        "min",
        "part_of_speech",
        "percent_rank",
        "percentile",
        "period_compare",
        "quality",
        "rank",
        "register",
        "relevance_info",
        "remainder",
        "score",
        "stddev",
        "stddev_p",
        "stem",
        "sum_aggregate",
        "thresholds",
        "tokenize",
        "train",
        "triple_value_statistics",
        "triples",
        "uri_match",
        "uris",
        "valid_document_patch_path",
        "valid_extract_path",
        "valid_index_path",
        "valid_optic_path",
        "valid_tde_context",
        "value_co_occurrences",
        "value_match",
        "value_ranges",
        "value_tuples",
        "values",
        "variance",
        "variance_p",
        "walk",
        "word_match",
        "words",
    ],
)
@respx.mock
async def test_result_operations_propagate_http_failure(name):
    # HTTP authorization fails before XQuery evaluation; no result type is faked.
    native = getattr(AsyncCtsService, name)
    required = {
        parameter: xs.string(parameter)
        for (parameter, item) in inspect.signature(native).parameters.items()
        if item.kind is not inspect.Parameter.VAR_KEYWORD
        and parameter != "self"
        and item.default is inspect.Parameter.empty
    }
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("txid", "txn")
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        with pytest.raises(httpx.HTTPStatusError):
            await getattr(AsyncCtsService(ml.rest), name)(
                **required,
                database="Documents",
                txid="txn",
                timeout=2,
            )
    assert route.call_count == 1
    for call in route.calls:
        data = parse_qs(call.request.content.decode())
        assert call.request.extensions["timeout"]["read"] == 2
        assert "cts:" + name.replace("_", "-") + "(" in data["xquery"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize("recognized", [False, True])
@respx.mock
async def test_result_services_preserve_shared_http_errors(recognized):
    response = (
        httpx.Response(
            400,
            json={
                "errorResponse": {
                    "statusCode": 400,
                    "status": "Bad Request",
                    "messageCode": "XDMP-UNDFUN",
                    "message": "Unknown function",
                },
            },
        )
        if recognized
        else httpx.Response(503, content=b"Proxy unavailable")
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(response.status_code)
    ml_mocker.with_response_body(response.content)
    for name, value in response.headers.items():
        ml_mocker.with_response_header(name, value)
    ml_mocker.mock_post()
    error = MarkLogicError if recognized else httpx.HTTPStatusError
    async with AsyncMLClient() as ml:
        with pytest.raises(error):
            await AsyncCtsService(ml.rest).search()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("count", "selection"),
    [
        (0, {}),
        (1, {}),
        (2, {}),
        (0, {"index": 1}),
        (1, {"index": 1}),
        (2, {"range": 2}),
    ],
)
@pytest.mark.parametrize("method", ["search", "collections"])
@respx.mock
async def test_result_cardinality_and_parsed_payloads(count, method, selection):
    parts = []
    for position in range(count):
        parts.extend(
            [
                MultipartPart({"Content-Type": "application/json"}, b"[1,2]")
                if method == "search"
                else MultipartPart(
                    {"Content-Type": "text/plain", "X-Primitive": "string"},
                    f"collection-{position}".encode(),
                ),
                MultipartPart(
                    {"Content-Type": "text/plain", "X-Primitive": "integer"},
                    str(0 if method == "search" else position + 1).encode(),
                ),
            ],
        )
    (body, content_type) = encode_multipart_mixed(parts)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(body)
    ml_mocker.with_response_header("Content-Type", content_type)
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        result = await getattr(AsyncCtsService(ml.rest), method)(**selection)
    model = SearchHit if method == "search" else ValueHit
    assert isinstance(result, list)
    assert len(result) == count
    items = result
    for position, item in enumerate(items):
        assert isinstance(item, model)
        assert (item.content if method == "search" else item.value) == (
            [1, 2] if method == "search" else f"collection-{position}"
        )
        assert (item.score if method == "search" else item.frequency) == (
            0 if method == "search" else position + 1
        )
    assert route.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("partner", [None, ("integer", b"bad"), "incomplete"])
@respx.mock
async def test_malformed_pairs_are_not_silently_accepted(partner):
    parts = [MultipartPart({"Content-Type": "application/xml"}, b"<a/>")]
    if partner == "incomplete":
        parts.extend(
            [
                MultipartPart(
                    {"Content-Type": "text/plain", "X-Primitive": "integer"},
                    b"1",
                ),
                MultipartPart({"Content-Type": "application/xml"}, b"<b/>"),
            ],
        )
    elif partner is not None:
        (primitive, value) = partner
        parts.append(
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": primitive},
                value,
            ),
        )
    (body, content_type) = encode_multipart_mixed(parts)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(body)
    ml_mocker.with_response_header("Content-Type", content_type)
    ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        with pytest.raises(ValueError, match=r"partner|invalid literal"):
            await AsyncCtsService(ml.rest).search()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["uris", "uri_match"])
@pytest.mark.parametrize(
    ("count", "selection"),
    [
        (0, {}),
        (1, {}),
        (2, {}),
        (0, {"index": 1}),
        (1, {"index": 1}),
        (2, {"range": 2}),
    ],
)
@respx.mock
async def test_uri_lookups_return_strings_without_frequency(method, count, selection):
    uris = [f"/{position}.xml" for position in range(count)]
    (body, content_type) = encode_multipart_mixed(
        [
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "string"},
                uri.encode(),
            )
            for uri in uris
        ],
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(body)
    ml_mocker.with_response_header("Content-Type", content_type)
    route = ml_mocker.mock_post()
    arguments = {"pattern": "/*.xml"} if method == "uri_match" else {}
    async with AsyncMLClient() as ml:
        assert (
            await getattr(AsyncCtsService(ml.rest), method)(**arguments, **selection)
            == uris
        )
    assert route.call_count == 1
    for call in route.calls:
        source = parse_qs(call.request.content.decode())["xquery"][0]
        assert "cts:frequency(" not in source


@pytest.mark.asyncio
@respx.mock
async def test_uris_empty_response_returns_empty_list():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": 'xquery version "1.0-ml";\ncts:uris()'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        assert await AsyncCtsService(ml.rest).uris() == []
    assert route.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("selection", [{}, {"index": 2}, {"range": [2, 3]}])
@respx.mock
async def test_async_search_projects_after_selection_with_shared_namespaces(selection):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(b"")
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        assert (
            await AsyncCtsService(
                ml.rest,
                namespaces={"p": "https://monasticus.com/mlclient/examples/old"},
            ).search(
                xpath="p:item/p:title",
                namespaces={"p": "https://monasticus.com/mlclient/examples/new"},
                **selection,
            )
            == []
        )
    body = parse_qs(route.calls.last.request.content.decode())
    source = body["xquery"][0]
    bindings = json.loads(body["vars"][0])
    assert (
        'declare namespace p = "https://monasticus.com/mlclient/examples/new";'
        in source
    )
    assert 'kind="xpath"' in source
    assert "cts:valid-extract-path(" in source
    assert "p:item/p:title" in bindings.values()
    assert "p:item/p:title" not in source
    template = next(value for value in bindings.values() if " ! " in value)
    assert "cts:search(/, ())" in template
    if selection:
        assert template.index("]") < template.index(" ! ")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "error"),
    [("", ValueError), ("  ", ValueError), (1, TypeError)],
)
@respx.mock
async def test_async_search_rejects_invalid_xpath_before_io(path, error):
    async with AsyncMLClient() as ml:
        with pytest.raises(error, match="xpath"):
            await AsyncCtsService(ml.rest).search(xpath=path)
    assert not respx.calls


@pytest.mark.asyncio
@respx.mock
async def test_async_lexicon_queries_require_explicit_keywords():
    async with AsyncMLClient() as ml:
        service = AsyncCtsService(ml.rest)
        with pytest.raises(TypeError):
            await service.uris(service.true_query())
        with pytest.raises(TypeError):
            await service.values(service.uri_reference(), service.true_query())
    assert not respx.calls


@pytest.mark.parametrize(
    ("operation", "native", "variables", "response", "expected"),
    [
        (("estimate", {}), "cts:estimate(())", {}, ("integer", "3"), 3),
        (
            ("estimate", {"maximum": 1}),
            "cts:estimate((), (), (), (), xs:double($v0))",
            {"v0": "1"},
            ("integer", "1"),
            1,
        ),
        (("uris", {}), "cts:uris()", {}, ("string", "/a.xml"), "/a.xml"),
        (
            ("uri_match", {"pattern": "/a*"}),
            "cts:uri-match($v0)",
            {"v0": "/a*"},
            ("string", "/a.xml"),
            "/a.xml",
        ),
        (
            (
                "contains",
                {
                    "nodes": StaticExpression("<p>coffee</p>"),
                    "query": lambda cts: cts.word_query("coffee"),
                },
            ),
            "cts:contains((<p>coffee</p>), cts:word-query($v0))",
            {"v0": "coffee"},
            ("boolean", "true"),
            True,
        ),
        (
            ("valid_extract_path", {"string": "/a"}),
            "cts:valid-extract-path($v0)",
            {"v0": "/a"},
            ("boolean", "true"),
            True,
        ),
        (
            ("valid_index_path", {"string": "/a", "ignorens": False}),
            "cts:valid-index-path($v0, $v1)",
            {"v0": "/a", "v1": False},
            ("boolean", "true"),
            True,
        ),
        (
            (
                "sum_aggregate",
                {"range_index": lambda cts: cts.field_reference("price")},
            ),
            "cts:sum-aggregate(cts:field-reference($v0))",
            {"v0": "price"},
            ("decimal", "3.75"),
            Decimal("3.75"),
        ),
        (
            (
                "count_aggregate",
                {"range_index": lambda cts: cts.field_reference("price")},
            ),
            "cts:count-aggregate(cts:field-reference($v0))",
            {"v0": "price"},
            ("unsignedLong", "2"),
            2,
        ),
        (
            ("min", {"range_index": lambda cts: cts.field_reference("price")}),
            "cts:min(cts:field-reference($v0))",
            {"v0": "price"},
            ("decimal", "1.25"),
            Decimal("1.25"),
        ),
        (
            ("max", {"range_index": lambda cts: cts.field_reference("price")}),
            "cts:max(cts:field-reference($v0))",
            {"v0": "price"},
            ("decimal", "2.50"),
            Decimal("2.50"),
        ),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_plain_result_operations(
    operation,
    native,
    variables,
    response,
    expected,
):
    method, arguments = operation
    primitive, payload = response
    scalar_type = "integer" if method == "estimate" else "string"
    declarations = "".join(
        f"declare variable ${name} as "
        f"xs:{'boolean' if isinstance(value, bool) else scalar_type} external;\n"
        for name, value in variables.items()
    )
    body = {"xquery": 'xquery version "1.0-ml";\n' + declarations + native}
    if variables:
        body["vars"] = json.dumps(variables)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(body)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(primitive, payload, "text/plain")
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        arguments = {
            name: value(cts) if callable(value) else value
            for name, value in arguments.items()
        }
        result = await getattr(cts, method)(**arguments)
    assert result == [expected]
    assert type(result[0]) is type(expected)
    assert route.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("output_type", "expected"),
    [(None, 3), (str, "3"), (bytes, b"3")],
)
@respx.mock
async def test_estimate_output_type_keeps_result_list(output_type, expected):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {"xquery": 'xquery version "1.0-ml";\ncts:estimate(())'},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("integer", "3", "text/plain")
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        result = await AsyncCtsService(ml.rest).estimate(output_type=output_type)
    assert result == [expected]
    assert type(result[0]) is type(expected)
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_estimate_rejects_invalid_output_type_before_io():
    async with AsyncMLClient() as ml:
        with pytest.raises(ValueError, match="output_type"):
            await AsyncCtsService(ml.rest).estimate(output_type=int)
    assert not respx.calls


@pytest.mark.parametrize(
    ("operation", "native", "variables", "response", "value"),
    [
        (
            ("values", {"range_indexes": lambda cts: cts.field_reference("price")}),
            "cts:values(cts:field-reference($v0))",
            {"v0": "price"},
            ("decimal", "1.25"),
            Decimal("1.25"),
        ),
        (
            ("field_values", {"field_names": "price"}),
            "cts:field-values($v0)",
            {"v0": "price"},
            ("decimal", "1.25"),
            Decimal("1.25"),
        ),
        (
            ("collections", {}),
            "cts:collections()",
            {},
            ("string", "products"),
            "products",
        ),
        (
            ("collection_match", {"pattern": "prod*"}),
            "cts:collection-match($v0)",
            {"v0": "prod*"},
            ("string", "products"),
            "products",
        ),
        (("words", {}), "cts:words()", {}, ("string", "coffee"), "coffee"),
        (
            ("word_match", {"pattern": "cof*"}),
            "cts:word-match($v0)",
            {"v0": "cof*"},
            ("string", "coffee"),
            "coffee",
        ),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_lexicon_values_include_frequency(
    operation,
    native,
    variables,
    response,
    value,
):
    method, arguments = operation
    primitive, payload = response
    declarations = "".join(
        f"declare variable ${name} as xs:string external;\n" for name in variables
    )
    source = (
        'xquery version "1.0-ml";\n' + declarations + f"for $res in {native}\n"
        "let $measure := cts:frequency($res)\n"
        "return ($res, $measure)"
    )
    body = {"xquery": source}
    if variables:
        body["vars"] = json.dumps(variables)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(body)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(primitive, payload, "text/plain")
    ml_mocker.with_response_body_part("integer", "3", "text/plain")
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        arguments = {
            name: value(cts) if callable(value) else value
            for name, value in arguments.items()
        }
        result = await getattr(cts, method)(**arguments)
    assert result == [ValueHit(value, frequency=3)]
    assert type(result[0].value) is type(value)
    assert route.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "arguments"),
    [
        ("values", {"range_indexes": lambda cts: cts.uri_reference()}),
        ("field_values", {"field_names": "price"}),
        ("collections", {}),
        ("words", {}),
    ],
)
@pytest.mark.parametrize(
    "options",
    ["map", ["map"], ("item-frequency", "map"), [xs.string("ascending"), ["map"]]],
)
@respx.mock
async def test_lexicon_map_options_are_rejected_before_io(method, arguments, options):
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        arguments = {
            name: value(cts) if callable(value) else value
            for name, value in arguments.items()
        }
        with pytest.raises(ValueError, match="Map output"):
            await getattr(cts, method)(
                **arguments,
                options=options,
            )


@pytest.mark.asyncio
@respx.mock
async def test_dynamic_lexicon_options_keep_server_map_validation():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "/a.xml", "text/plain")
    ml_mocker.with_response_body_part("integer", "1", "text/plain")
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        result = await cts.values(
            cts.uri_reference(),
            options=[xs.string("item-frequency")],
        )

    assert result == [ValueHit("/a.xml", frequency=1)]
    source = parse_qs(route.calls.last.request.content.decode())["xquery"][0]
    assert "return if ($res instance of map:map) then" in source
    assert "MLCLIENT-LEXICON-MAP" in source
    assert "else\n    let $measure := cts:frequency($res)" in source


@pytest.mark.asyncio
@respx.mock
async def test_search_pairs_results_without_a_redundant_inner_loop():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": 'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "for $res in cts:search(/, cts:word-query($v0))\n"
            "let $measure := cts:score($res)\n"
            "return ($res, $measure)",
            "vars": json.dumps({"v0": "coffee"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        assert await cts.search(query=cts.word_query("coffee")) == []
    assert route.call_count == 1


@pytest.mark.parametrize("method", ["search", "values", "uris"])
@pytest.mark.asyncio
@respx.mock
async def test_index_and_range_are_mutually_exclusive(method):
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        arguments = {"range_indexes": cts.uri_reference()} if method == "values" else {}
        with pytest.raises(ValueError, match="mutually exclusive"):
            await getattr(cts, method)(
                **arguments,
                index=1,
                range=[1, 2],
            )
    assert not respx.calls


@pytest.mark.parametrize("selection", [{"range": [1, 2]}, {"index": fn.last()}])
@pytest.mark.asyncio
@respx.mock
async def test_values_selection_returns_a_single_item_list(selection):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "/a.xml", "text/plain")
    ml_mocker.with_response_body_part("integer", "1", "text/plain")
    route = ml_mocker.mock_post()
    async with AsyncMLClient() as ml:
        cts = AsyncCtsService(ml.rest)
        result = await cts.values(cts.uri_reference(), **selection)
    assert result == [ValueHit("/a.xml", frequency=1)]
    body = parse_qs(route.calls.last.request.content.decode())
    assert "cts:values(cts:uri-reference())" in body["xquery"][0]
    assert (
        "[fn:last()]" in body["xquery"][0]
        if "index" in selection
        else "[$v0 to $v1]" in body["xquery"][0]
    )
