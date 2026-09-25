from __future__ import annotations

import inspect
import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.functions.xqy import Cts, XqyExpression, fn, xdmp, xpath, xs
from mlclient.models import SearchHit, ValueHit
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.responses import MLResponseParser
from mlclient.services import AsyncCtsService, CtsService


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
async def test_result_operations_execute_once_sync_and_async(name):
    native = getattr(Cts, name)
    required = {
        parameter: xs.string(parameter)
        for parameter, item in inspect.signature(native).parameters.items()
        if item.default is inspect.Parameter.empty
    }
    service_arguments = dict(required)
    parts = [
        MultipartPart({"Content-Type": "text/plain", "X-Primitive": "integer"}, b"7"),
    ]
    if name in VALUE_OPERATIONS:
        parts.append(
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "integer"},
                b"3",
            ),
        )
    body, content_type = encode_multipart_mixed(parts)
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(
            200,
            content=body,
            headers={"Content-Type": content_type},
        ),
    )
    with MLClient() as ml:
        result = getattr(CtsService(ml.rest), name)(
            **service_arguments,
            database="Documents",
            txid="txn",
            timeout=2,
        )
    async with AsyncMLClient() as ml:
        async_result = await getattr(AsyncCtsService(ml.rest), name)(
            **service_arguments,
            database="Documents",
            txid="txn",
            timeout=2,
        )
    for actual in (result, async_result):
        assert not isinstance(actual, XqyExpression)
        if name in VALUE_OPERATIONS:
            assert actual.content == 7
            assert actual.frequency == 3
        else:
            assert actual == 7
    assert route.call_count == 2
    for call in route.calls:
        data = parse_qs(call.request.content.decode())
        assert call.request.url.params["database"] == "Documents"
        assert call.request.url.params["txid"] == "txn"
        assert call.request.extensions["timeout"]["read"] == 2
        assert "cts:" + name.replace("_", "-") + "(" in data["xquery"][0]
        if name not in VALUE_OPERATIONS:
            source, variables = native(**required).compile()
            assert data["xquery"] == [source]
            if variables:
                assert json.loads(data["vars"][0]) == variables


@respx.mock
def test_service_parses_once_before_return_and_retains_original_bytes(monkeypatch):
    original = b'{ "a" : [1, 2] }'
    body, content_type = encode_multipart_mixed(
        [
            MultipartPart(
                {
                    "Content-Type": "application/json",
                    "X-Primitive": "object-node()",
                    "X-URI": "/a.json",
                },
                original,
            ),
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": "integer"},
                b"0",
            ),
        ],
    )
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(
            200,
            content=body,
            headers={"Content-Type": content_type},
        ),
    )
    parser = MLResponseParser.parse_part
    calls = []

    def counted_parse(part):
        calls.append(part)
        return parser(part)

    monkeypatch.setattr(MLResponseParser, "parse_part", counted_parse)
    with MLClient() as ml:
        hit = CtsService(ml.rest).search(index=1)
    assert len(calls) == 1
    assert hit.content == {"a": [1, 2]}
    assert hit.content_bytes == original
    assert hit.content_string == original.decode()
    assert hit.source_uri == "/a.json"
    assert hit.source_path == "/"
    hit.content["a"].append(3)
    assert hit.content_bytes == original
    assert len(calls) == 1
    assert route.call_count == 1


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
    respx.post("http://localhost:8000/v1/eval").mock(return_value=response)
    error = MarkLogicError if recognized else httpx.HTTPStatusError
    with MLClient() as ml, pytest.raises(error):
        CtsService(ml.rest).search()
    async with AsyncMLClient() as ml:
        with pytest.raises(error):
            await AsyncCtsService(ml.rest).search()


@respx.mock
def test_result_services_reject_raw_output_before_io():
    with MLClient() as ml, pytest.raises(TypeError, match="output_type"):
        CtsService(ml.rest).search(output_type=bytes)
    assert not respx.calls


def test_every_catalog_function_has_an_explicit_execution_policy():
    names = {name for name, method in inspect.getmembers(Cts, inspect.isfunction)}
    assert names == BUILDERS | VALUE_OPERATIONS | PLAIN_OPERATIONS | {"search"}
    assert not BUILDERS & (VALUE_OPERATIONS | PLAIN_OPERATIONS)
    assert not VALUE_OPERATIONS & PLAIN_OPERATIONS
    for name in BUILDERS:
        assert getattr(CtsService, name) is getattr(Cts, name)
        assert getattr(AsyncCtsService, name) is getattr(Cts, name)
    for name in VALUE_OPERATIONS | PLAIN_OPERATIONS | {"search"}:
        assert name in CtsService.__dict__
        assert name in AsyncCtsService.__dict__
        assert inspect.iscoroutinefunction(getattr(AsyncCtsService, name))
        native_parameters = inspect.signature(getattr(Cts, name)).parameters
        for cls in (CtsService, AsyncCtsService):
            parameters = inspect.signature(getattr(cls, name)).parameters
            assert [key for key in parameters if key in native_parameters] == list(
                native_parameters,
            )
            for key, parameter in native_parameters.items():
                assert parameters[key].kind == parameter.kind
                assert parameters[key].default == parameter.default


# Explicit semantic inventory; every native function must be classified.
BUILDERS = {
    "after_query",
    "and_not_query",
    "and_query",
    "before_query",
    "boost_query",
    "box",
    "circle",
    "collection_query",
    "collection_reference",
    "column_range_query",
    "complex_polygon",
    "confidence_order",
    "directory_query",
    "document_format_query",
    "document_fragment_query",
    "document_order",
    "document_permission_query",
    "document_query",
    "document_root_query",
    "element_attribute_pair_geospatial_query",
    "element_attribute_range_query",
    "element_attribute_reference",
    "element_attribute_value_query",
    "element_attribute_word_query",
    "element_child_geospatial_query",
    "element_geospatial_query",
    "element_pair_geospatial_query",
    "element_query",
    "element_range_query",
    "element_reference",
    "element_value_query",
    "element_word_query",
    "entity",
    "entity_dictionary",
    "entity_dictionary_parse",
    "false_query",
    "field_range_query",
    "field_reference",
    "field_value_query",
    "field_word_query",
    "fitness_order",
    "geospatial_attribute_pair_reference",
    "geospatial_element_child_reference",
    "geospatial_element_pair_reference",
    "geospatial_element_reference",
    "geospatial_json_property_child_reference",
    "geospatial_json_property_pair_reference",
    "geospatial_json_property_reference",
    "geospatial_path_reference",
    "geospatial_region_path_reference",
    "geospatial_region_query",
    "index_order",
    "iri_reference",
    "json_property_child_geospatial_query",
    "json_property_geospatial_query",
    "json_property_pair_geospatial_query",
    "json_property_range_query",
    "json_property_reference",
    "json_property_scope_query",
    "json_property_value_query",
    "json_property_word_query",
    "linestring",
    "locks_fragment_query",
    "lsqt_query",
    "near_query",
    "not_in_query",
    "not_query",
    "or_query",
    "parse",
    "path_geospatial_query",
    "path_range_query",
    "path_reference",
    "period",
    "period_compare_query",
    "period_range_query",
    "point",
    "polygon",
    "properties_fragment_query",
    "quality_order",
    "query",
    "range_query",
    "reference_parse",
    "registered_query",
    "reverse_query",
    "score_order",
    "similar_query",
    "triple_range_query",
    "true_query",
    "unordered",
    "uri_reference",
    "word_query",
}

VALUE_OPERATIONS = {
    "collection_match",
    "collections",
    "element_attribute_pair_geospatial_boxes",
    "element_attribute_pair_geospatial_value_match",
    "element_attribute_pair_geospatial_values",
    "element_attribute_value_match",
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
    "element_value_match",
    "element_values",
    "element_word_match",
    "element_words",
    "field_value_match",
    "field_values",
    "field_word_match",
    "field_words",
    "geospatial_boxes",
    "json_property_word_match",
    "json_property_words",
    "uri_match",
    "uris",
    "value_match",
    "values",
    "word_match",
    "words",
}

PLAIN_OPERATIONS = {
    "aggregate",
    "avg_aggregate",
    "classify",
    "cluster",
    "confidence",
    "contains",
    "correlation",
    "count_aggregate",
    "covariance",
    "covariance_p",
    "deregister",
    "distinctive_terms",
    "element_attribute_value_co_occurrences",
    "element_attribute_value_geospatial_co_occurrences",
    "element_attribute_value_ranges",
    "element_value_co_occurrences",
    "element_value_geospatial_co_occurrences",
    "element_value_ranges",
    "element_walk",
    "entity_dictionary_get",
    "entity_highlight",
    "entity_walk",
    "estimate",
    "field_value_co_occurrences",
    "field_value_ranges",
    "fitness",
    "frequency",
    "geospatial_co_occurrences",
    "highlight",
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
    "valid_document_patch_path",
    "valid_extract_path",
    "valid_index_path",
    "valid_optic_path",
    "valid_tde_context",
    "value_co_occurrences",
    "value_ranges",
    "value_tuples",
    "variance",
    "variance_p",
    "walk",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [0, 1, 2])
@pytest.mark.parametrize("method", ["search", "uris"])
@pytest.mark.parametrize("selection", [{}, {"index": 1}, {"range": 2}])
@respx.mock
async def test_result_cardinality_and_parsed_payloads(count, method, selection):
    parts = []
    for position in range(count):
        parts.extend(
            [
                MultipartPart({"Content-Type": "application/json"}, b"[1,2]"),
                MultipartPart(
                    {"Content-Type": "text/plain", "X-Primitive": "integer"},
                    str(position).encode(),
                ),
            ],
        )
    body, content_type = encode_multipart_mixed(parts)
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(
            200,
            content=body,
            headers={"Content-Type": content_type},
        ),
    )
    with MLClient() as ml:
        result = getattr(CtsService(ml.rest), method)(**selection)
    async with AsyncMLClient() as ml:
        async_result = await getattr(AsyncCtsService(ml.rest), method)(**selection)
    model = SearchHit if method == "search" else ValueHit
    for actual in (result, async_result):
        if count == 1:
            assert isinstance(actual, model)
            items = [actual]
        else:
            assert isinstance(actual, list)
            assert len(actual) == count
            items = actual
        for position, item in enumerate(items):
            assert item.content_bytes == b"[1,2]"
            assert item.content == [1, 2]
            assert (item.score if method == "search" else item.frequency) == position
    assert route.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("partner", [None, ("string", b"1"), ("integer", b"bad")])
@respx.mock
async def test_malformed_pairs_are_not_silently_accepted(partner):
    parts = [MultipartPart({"Content-Type": "application/xml"}, b"<a/>")]
    if partner is not None:
        primitive, value = partner
        parts.append(
            MultipartPart(
                {"Content-Type": "text/plain", "X-Primitive": primitive},
                value,
            ),
        )
    body, content_type = encode_multipart_mixed(parts)
    respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(
            200,
            content=body,
            headers={"Content-Type": content_type},
        ),
    )
    with MLClient() as ml, pytest.raises(ValueError, match=r"partner|invalid literal"):
        CtsService(ml.rest).search()
    async with AsyncMLClient() as ml:
        with pytest.raises(ValueError, match=r"partner|invalid literal"):
            await AsyncCtsService(ml.rest).search()


@pytest.mark.parametrize("selection", [{}, {"index": 2}, {"range": [2, 3]}])
@respx.mock
def test_search_projects_after_selection_with_shared_namespaces(selection):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, content=b""),
    )
    with MLClient() as ml:
        assert (
            CtsService(ml.rest, namespaces={"p": "urn:old"}).search(
                xpath="p:item/p:title",
                namespaces={"p": "urn:new"},
                **selection,
            )
            == []
        )
    body = parse_qs(route.calls.last.request.content.decode())
    source = body["xquery"][0]
    bindings = json.loads(body["vars"][0])
    assert 'declare namespace p = "urn:new";' in source
    assert 'kind="projection"' in source
    assert "cts:valid-extract-path(" in source
    assert "p:item/p:title" in bindings.values()
    assert "p:item/p:title" not in source
    template = next(value for value in bindings.values() if " ! (" in value)
    assert "cts:search((/), ())" in template
    if selection:
        assert template.index("]") < template.index(" ! (")


@pytest.mark.asyncio
@pytest.mark.parametrize("selection", [{}, {"index": 2}, {"range": [2, 3]}])
@respx.mock
async def test_async_search_projects_after_selection_with_shared_namespaces(selection):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, content=b""),
    )
    async with AsyncMLClient() as ml:
        assert (
            await AsyncCtsService(ml.rest, namespaces={"p": "urn:old"}).search(
                xpath="p:item/p:title",
                namespaces={"p": "urn:new"},
                **selection,
            )
            == []
        )
    body = parse_qs(route.calls.last.request.content.decode())
    source = body["xquery"][0]
    bindings = json.loads(body["vars"][0])
    assert 'declare namespace p = "urn:new";' in source
    assert 'kind="projection"' in source
    assert "cts:valid-extract-path(" in source
    assert "p:item/p:title" in bindings.values()
    assert "p:item/p:title" not in source
    template = next(value for value in bindings.values() if " ! (" in value)
    assert "cts:search((/), ())" in template
    if selection:
        assert template.index("]") < template.index(" ! (")


@pytest.mark.parametrize(
    ("path", "error"),
    [("", ValueError), ("  ", ValueError), (1, TypeError)],
)
@respx.mock
def test_search_rejects_invalid_projection_before_io(path, error):
    with MLClient() as ml, pytest.raises(error, match="xpath"):
        CtsService(ml.rest).search(xpath=path)
    assert not respx.calls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "error"),
    [("", ValueError), ("  ", ValueError), (1, TypeError)],
)
@respx.mock
async def test_async_search_rejects_invalid_projection_before_io(path, error):
    async with AsyncMLClient() as ml:
        with pytest.raises(error, match="xpath"):
            await AsyncCtsService(ml.rest).search(xpath=path)
    assert not respx.calls


@respx.mock
def test_lexicon_queries_require_explicit_keywords():
    with MLClient() as ml:
        service = CtsService(ml.rest)
        with pytest.raises(TypeError):
            service.uris(service.true_query())
        with pytest.raises(TypeError):
            service.values(service.uri_reference(), service.true_query())
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


def _response(*items):
    parts = [
        MultipartPart({"Content-Type": mime, "X-Primitive": primitive}, value.encode())
        for primitive, mime, value in items
    ]
    body, content_type = encode_multipart_mixed(parts)
    return httpx.Response(200, content=body, headers={"Content-Type": content_type})


@pytest.mark.asyncio
@respx.mock
async def test_async_expression_and_all_conveniences_share_execution_contract():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("integer", "text/plain", "1")),
    )
    async with AsyncMLClient() as ml:
        assert await ml.eval.expression(xs.integer(1)) == 1
        route.mock(return_value=_response(*[("integer", "text/plain", "1")] * 2))
        cts = AsyncCtsService(ml.rest)
        assert (await cts.search(query=Cts.true_query(), range=1)).content == 1
        assert (await cts.uris(range=[1, 2])).content == 1
        assert (await cts.values(Cts.uri_reference(), range=1)).content == 1
        assert (await cts.search(index=1)).content == 1
        assert (await cts.uris(index=fn.last())).content == 1
        assert (await cts.values(Cts.uri_reference(), index=1)).content == 1
        with pytest.raises(ValueError, match="mutually exclusive"):
            await cts.search(index=1, range=[1, 2])
        route.mock(return_value=_response(("integer", "text/plain", "1")))
        assert await cts.estimate(maximum=1) == 1
        assert await ml.eval.expression(fn.count([1], maximum=1)) == 1
        route.mock(return_value=_response(("boolean", "text/plain", "true")))
        assert await ml.eval.expression(fn.exists([1])) is True
        assert await ml.eval.expression(fn.empty([])) is True
        assert await ml.eval.expression(xdmp.exists(xpath("/"))) is True


@respx.mock
def test_sync_conveniences_share_result_cardinality():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(*[("integer", "text/plain", "1")] * 2),
    )
    with MLClient() as ml:
        cts = CtsService(ml.rest)
        assert cts.word_query("cat").compile() == Cts.word_query("cat").compile()
        assert cts.search(range=1).content == 1
        assert cts.uris(range=[1, 2]).content == 1
        assert cts.values(Cts.uri_reference()).content == 1
        assert cts.search(index=1).content == 1
        assert cts.uris(index=fn.last()).content == 1
        assert cts.values(Cts.uri_reference(), index=1).content == 1
        with pytest.raises(ValueError, match="mutually exclusive"):
            cts.uris(index=1, range=[1, 2])
        route.mock(return_value=_response(("integer", "text/plain", "1")))
        assert cts.estimate() == 1
        assert ml.eval.expression(fn.count([1])) == 1
        route.mock(return_value=_response(("boolean", "text/plain", "true")))
        assert ml.eval.expression(fn.exists([1])) is True
        assert ml.eval.expression(fn.empty([])) is True
        assert ml.eval.expression(xdmp.exists(xpath("/"))) is True
        route.mock(return_value=_response())
        with pytest.raises(TypeError, match="exactly one"):
            cts.estimate()


@pytest.mark.parametrize("value", [True, 1.5, (1,), (1, 2, 3), [1], [1, 2, 3]])
@respx.mock
def test_service_range_validation_happens_before_io(value):
    with MLClient() as ml, pytest.raises(TypeError, match="range"):
        CtsService(ml.rest).search(range=value)
    assert not respx.calls
