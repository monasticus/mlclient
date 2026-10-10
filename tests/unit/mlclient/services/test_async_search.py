from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError
from mlclient.services import SearchScope
from mlclient.xquery import cts
from mlclient.models import JSONDocument, SearchReport, TupleHit, ValueHit, XMLDocument
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element, sq
from tests.utils import data as test_data, resources as resources_utils
from tests.utils.data import MetadataSpec
from tests.utils.ml_mockers import MLRespXMocker

SEARCH_URL = "http://localhost:8000/v1/search"
VALUES_URL = "http://localhost:8000/v1/values/category"
CTS_QUERY = resources_utils.read_query_input(__file__, "cts-query.py")
CTS_BODY = resources_utils.get_test_resource_json(__file__, "cts-body.json")
CTS_XML = resources_utils.read_test_resource_text(__file__, "cts-query.xml")
ERROR_RESPONSE = resources_utils.get_test_resource_json(__file__, "error-response.json")


@pytest.mark.asyncio
@respx.mock
async def test_documents_for_cts_query():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.xml_doc_body_part("/products/coffee.xml"),
    )
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(CTS_BODY)
    route = ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents(CTS_QUERY)

    assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
    assert [doc.uri for doc in docs] == [
        "/products/coffee.xml",
        "/products/coffee.json",
    ]
    assert docs[1].content == {"root": {"child": "data"}}
    assert dict(route.calls.last.request.url.params) == {
        "format": "json",
    }


@pytest.mark.asyncio
@respx.mock
async def test_documents_for_structured_query():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-104.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents(
            resources_utils.read_query_input(__file__, "structured-query.py"),
        )

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@pytest.mark.asyncio
@respx.mock
async def test_documents_for_string_query():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-122.json"),
    )
    route = ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents("coffee AND tea")

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]
    assert "structuredQuery" not in route.calls.last.request.url.params


@pytest.mark.asyncio
@respx.mock
async def test_documents_without_query():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-139.json"),
    )
    route = ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents()

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]
    assert dict(route.calls.last.request.url.params) == {"format": "json"}


@pytest.mark.asyncio
@respx.mock
async def test_documents_at_single_position():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("start", "3")
    ml_mocker.with_request_param("pageLength", "1")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-156.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents("coffee", pos=3)

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@pytest.mark.asyncio
@respx.mock
async def test_documents_in_position_range():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("start", "11")
    ml_mocker.with_request_param("pageLength", "10")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-172.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents("coffee", pos=(11, 20))

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@pytest.mark.asyncio
@respx.mock
async def test_documents_with_metadata():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("category", "content")
    ml_mocker.with_request_param("category", "collections")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.doc_metadata_body_part(
            "/products/coffee.json",
            MetadataSpec(collections=["products"]),
        ),
    )
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-197.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents("coffee", category=["content", "collections"])

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]
    assert docs[0].content == {"root": {"child": "data"}}
    assert docs[0].metadata.collections() == ["products"]


@pytest.mark.asyncio
@respx.mock
async def test_documents_forwards_options_database_and_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("txid", "12345")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-219.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        scoped = ml.search(
            database="Documents",
            txid="12345",
            options="product-options",
        )
        docs = await scoped.documents("coffee")

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@pytest.mark.asyncio
@respx.mock
async def test_documents_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("vnd.marklogic.result-estimate", "0")
    ml_mocker.with_empty_response_body()
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-239.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        docs = await ml.search.documents("zzz")

    assert docs == []


@pytest.mark.asyncio
@respx.mock
async def test_documents_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ERROR_RESPONSE)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-255.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        with pytest.raises(MarkLogicError) as error:
            await ml.search.documents("coffee")

    assert "REST-INVALIDPARAM" in str(error.value)


@pytest.mark.asyncio
@respx.mock
async def test_uris():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.doc_metadata_body_part(
            "/products/coffee.xml",
            MetadataSpec(quality=0),
        ),
    )
    ml_mocker.with_response_documents_body_part(
        test_data.doc_metadata_body_part(
            "/products/coffee.json",
            MetadataSpec(quality=0),
        ),
    )
    ml_mocker.with_request_body(CTS_BODY)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        uris = await ml.search.uris(CTS_QUERY, pos=[2, 3])

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@pytest.mark.asyncio
@respx.mock
async def test_uris_of_single_match():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.doc_metadata_body_part(
            "/products/coffee.json",
            MetadataSpec(quality=0),
        ),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-305.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        uris = await ml.search.uris("coffee")

    assert uris == ["/products/coffee.json"]


@pytest.mark.asyncio
@respx.mock
async def test_uris_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-319.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        uris = await ml.search.uris("zzz")

    assert uris == []


@pytest.mark.asyncio
@respx.mock
async def test_uris_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ERROR_RESPONSE)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-335.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        with pytest.raises(MarkLogicError) as error:
            await ml.search.uris()

    assert "REST-INVALIDPARAM" in str(error.value)


@pytest.mark.asyncio
@respx.mock
async def test_values_of_strings():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {
            "values-response": {
                "name": "category",
                "type": "xs:string",
                "distinct-value": [
                    {"frequency": 2, "_value": "drinks"},
                    {"frequency": 1, "_value": "food"},
                ],
            },
        },
    )
    ml_mocker.with_request_body(
        {"search": {"options": {"additional-query": [CTS_XML]}}},
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        products = ml.search(options="product-options")
        values = await products.values("category", CTS_QUERY)

    assert values == [
        ValueHit("drinks", frequency=2),
        ValueHit("food", frequency=1),
    ]


@pytest.mark.parametrize(
    ("atomic_type", "lexical", "expected"),
    [
        ("xs:decimal", "4.50", Decimal("4.50")),
        ("xs:int", "7", 7),
        ("xs:double", "1.5E2", 150.0),
        ("xs:date", "2026-01-02", date(2026, 1, 2)),
        ("xs:anyURI", "/a.json", "/a.json"),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_values_are_converted_from_their_type(atomic_type, lexical, expected):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "1")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {
            "values-response": {
                "type": atomic_type,
                "distinct-value": [{"frequency": 3, "_value": lexical}],
            },
        },
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-402.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        values = await ml.search.values("category", "coffee", pos=1)

    assert values == [ValueHit(expected, frequency=3)]
    assert type(values[0].value) is type(expected)


@pytest.mark.asyncio
@respx.mock
async def test_values_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("txid", "12345")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {"values-response": {"name": "category", "type": "xs:string"}},
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-419.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        values = await ml.search(database="Documents", txid="12345").values("category")

    assert values == []


@pytest.mark.asyncio
@respx.mock
async def test_values_reject_tuples():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {"values-response": {"name": "category", "tuple": [{"frequency": 1}]}},
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-435.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        with pytest.raises(ValueError, match=r"use tuples\(\)") as error:
            await ml.search.values("category")

    assert str(error.value) == (
        "values() reads values definitions; use tuples() for co-occurrences"
    )


@pytest.mark.asyncio
@respx.mock
async def test_values_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(ERROR_RESPONSE)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-453.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        with pytest.raises(MarkLogicError) as error:
            await ml.search.values("category")

    assert "REST-INVALIDPARAM" in str(error.value)


@pytest.mark.parametrize(
    ("pos", "error_type", "message"),
    [
        (0, ValueError, "pos must satisfy 1 <= start <= end"),
        ([5, 4], ValueError, "pos must satisfy 1 <= start <= end"),
        ([1, 2, 3], TypeError, "pos ranges must contain exactly two positions"),
        ("1", TypeError, "pos positions must be integers"),
        ([1, True], TypeError, "pos positions must be integers"),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_invalid_pos_is_rejected_before_request(pos, error_type, message):
    async with AsyncMLClient() as ml:
        with pytest.raises(error_type) as error:
            await ml.search.documents("coffee", pos=pos)

    assert str(error.value) == message


@pytest.mark.asyncio
@respx.mock
async def test_invalid_query_is_rejected_before_request():
    async with AsyncMLClient() as ml:
        with pytest.raises(TypeError) as error:
            await ml.search.uris({"q": "coffee"})

    assert str(error.value) == "query must be a SearchQuery, a string query or None"


# ML12 captures for prices 1.25/2.5 and dates 2026-01-01/2026-01-02.
# Integer-average capture uses quantities 2/3. Volatile timing metrics omitted.
PRICE_OPTIONS = {
    "values": [
        {
            "name": "price",
            "range": {
                "type": "xs:decimal",
                "element": {"ns": "", "name": "price"},
            },
        },
    ],
}


@pytest.mark.parametrize(
    ("name", "scalar_type", "function", "lexical", "expected"),
    [
        ("price", "xs:decimal", "sum", "3.75", Decimal("3.75")),
        ("price", "xs:decimal", "avg", "1.875", Decimal("1.875")),
        ("price", "xs:decimal", "count", "2", 2),
        ("price", "xs:decimal", "stddev", "0.883883476483185", 0.883883476483185),
        ("price", "xs:decimal", "median", "1.875", 1.875),
        ("price", "xs:decimal", "max", "2.5", Decimal("2.5")),
        ("quantity", "xs:int", "avg", "2.5", Decimal("2.5")),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_aggregate_native_result(name, scalar_type, function, lexical, expected):
    options = {
        "values": [
            {
                "name": name,
                "range": {
                    "type": scalar_type,
                    "element": {"ns": "", "name": name},
                },
            },
        ],
    }
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("aggregate", function)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url(f"http://localhost:8000/v1/values/{name}")
    ml_mocker.with_request_body({"search": {"options": options}})
    ml_mocker.with_response_body(
        {
            "values-response": {
                "name": name,
                "type": scalar_type,
                "aggregate-result": [{"name": function, "_value": lexical}],
            },
        },
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.search(options=options).aggregate(name, function)

    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.asyncio
@respx.mock
async def test_aggregate_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price")
    ml_mocker.with_request_body({"search": {"options": PRICE_OPTIONS, "qtext": "zzz"}})
    ml_mocker.with_response_body(
        {
            "values-response": {
                "name": "price",
                "type": "xs:decimal",
                "aggregate-result": [{"name": "avg"}],
            },
        },
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        result = await ml.search(options=PRICE_OPTIONS).aggregate("price", "avg", "zzz")

    assert result is None


@pytest.mark.parametrize(
    ("query", "fragment"),
    [
        ("zzz", {"qtext": "zzz"}),
        (
            cts.word_query("zzz"),
            {
                "options": {
                    **PRICE_OPTIONS,
                    "additional-query": [
                        (
                            '<cts:word-query xmlns:cts="http://marklogic.com/cts"><c'
                            "ts:text>zzz</cts:text></cts:word-query>"
                        ),
                    ],
                },
            },
        ),
        (sq.term("zzz"), {"query": {"queries": [{"term-query": {"text": ["zzz"]}}]}}),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_inline_options_with_query(query, fragment):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price")
    ml_mocker.with_request_body({"search": {"options": PRICE_OPTIONS, **fragment}})
    ml_mocker.with_response_body(
        {"values-response": {"name": "price", "type": "xs:decimal"}},
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        assert await ml.search(options=PRICE_OPTIONS).values("price", query) == []


@pytest.mark.asyncio
@respx.mock
async def test_values_with_options_builder_and_controls():
    options = SearchOptions().values("price", Range(Element("price"), "xs:decimal"))
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("direction", "descending")
    ml_mocker.with_request_param("frequency", "fragment")
    ml_mocker.with_request_param("limit", "1")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price")
    ml_mocker.with_request_body({"search": {"options": PRICE_OPTIONS}})
    ml_mocker.with_response_body(
        {
            "values-response": {
                "name": "price",
                "type": "xs:decimal",
                "distinct-value": [{"frequency": 1, "_value": "2.5"}],
            },
        },
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        values = await ml.search(options=options).values(
            "price",
            direction="descending",
            frequency="fragment",
            limit=1,
        )

    assert values == [ValueHit(Decimal("2.5"), frequency=1)]


@pytest.mark.asyncio
async def test_invalid_options():
    async with AsyncMLClient() as ml:
        with pytest.raises(TypeError) as error:
            await ml.search(options=123).values("price")

    assert str(error.value) == (
        "options must be an installed name, inline dictionary or SearchOptions, got int"
    )


@pytest.mark.asyncio
@respx.mock
async def test_tuples_have_individual_types():
    options = SearchOptions().tuples(
        "price-day",
        Range(Element("price"), "xs:decimal"),
        Range(Element("day"), "xs:date"),
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-677.json"),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    # ML10 XML capture; timing metrics omitted.
    ml_mocker.with_response_body("""<search:values-response name="price-day"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:search="http://marklogic.com/appservices/search">
  <search:tuple frequency="1">
    <search:distinct-value xsi:type="xs:decimal">1.25</search:distinct-value>
    <search:distinct-value xsi:type="xs:date">2026-01-01</search:distinct-value>
  </search:tuple>
  <search:tuple frequency="1">
    <search:distinct-value xsi:type="xs:decimal">2.5</search:distinct-value>
    <search:distinct-value xsi:type="xs:date">2026-01-02</search:distinct-value>
  </search:tuple>
</search:values-response>""")
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        tuples = await ml.search(options=options).tuples("price-day")

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@pytest.mark.asyncio
@respx.mock
async def test_tuples_reject_values_definition():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body({"search": {"options": PRICE_OPTIONS}})
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body("""<search:values-response name="price"
    type="xs:decimal"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:search="http://marklogic.com/appservices/search">
  <search:distinct-value frequency="1">1.25</search:distinct-value>
  <search:distinct-value frequency="1">2.5</search:distinct-value>
</search:values-response>""")
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        with pytest.raises(ValueError, match="tuples definitions") as error:
            await ml.search(options=PRICE_OPTIONS).tuples("price")

    assert (
        str(error.value)
        == "tuples() reads tuples definitions; use values() for single values"
    )


@pytest.mark.asyncio
@respx.mock
async def test_report_retains_empty_native_report_and_timestamp():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_header("ML-Effective-Timestamp", "17912992738350300")
    payload = {
        "snippet-format": "snippet",
        "total": 0,
        "start": 1,
        "page-length": 10,
        "results": [],
        "qtext": "product",
        "metrics": {"query-resolution-time": "PT0.001417S", "total-time": "PT0.00169S"},
    }
    ml_mocker.with_response_body(payload)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "request-775.json"),
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        report = await ml.search.report("product")

    assert report == SearchReport(
        total=0,
        start=1,
        page_length=10,
        results=[],
        facets={},
        metrics=payload["metrics"],
        effective_timestamp="17912992738350300",
        response=payload,
    )


@pytest.mark.parametrize(
    ("operation", "args", "operation_params", "accept", "response_format"),
    [
        ("documents", ("zzz",), {}, "multipart/mixed", "json"),
        ("uris", ("zzz",), {"category": "quality"}, "multipart/mixed", "json"),
        (
            "values",
            ("price", "zzz"),
            {
                "view": "values",
                "direction": "descending",
                "frequency": "fragment",
                "limit": "0",
            },
            "application/json",
            "json",
        ),
        (
            "aggregate",
            ("price", "sum", "zzz"),
            {
                "view": "aggregate",
                "aggregate": "sum",
                "direction": "descending",
                "frequency": "fragment",
                "limit": "0",
            },
            "application/json",
            "json",
        ),
        (
            "tuples",
            ("price", "zzz"),
            {
                "view": "values",
                "direction": "descending",
                "frequency": "fragment",
                "limit": "0",
            },
            "application/xml",
            "xml",
        ),
        ("report", ("zzz",), {"view": "all"}, "application/json", "json"),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_operation_forwards_all_controls_and_transaction_error(
    operation,
    args,
    operation_params,
    accept,
    response_format,
):
    ml_mocker = MLRespXMocker(use_router=False)
    url = VALUES_URL.replace("/category", "/price") if len(args) > 1 else SEARCH_URL
    ml_mocker.with_url(url)
    expected_params = {
        "format": response_format,
        "start": "1",
        "pageLength": "2",
        "database": "Documents",
        "txid": "12345",
        "directory": "/probe/",
        "timestamp": "0",
        **operation_params,
    }
    transforms = operation in {"documents", "report"}
    if transforms:
        expected_params["transform"] = "missing"
    for name, value in expected_params.items():
        ml_mocker.with_request_param(name, value)
    ml_mocker.with_request_param("collection", "probe")
    ml_mocker.with_request_param("collection", "other")
    ml_mocker.with_request_param("forest-name", "Documents")
    ml_mocker.with_request_param("forest-name", "Modules")
    if transforms:
        ml_mocker.with_request_param("trans:offset", "0")
    ml_mocker.with_request_header("Accept", accept)
    ml_mocker.with_request_body({"search": {"qtext": "zzz", "options": PRICE_OPTIONS}})
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type(
        f"application/{response_format}; charset=UTF-8",
    )
    # ML10 transaction-not-found captures, before any query evaluation.
    captures = {
        "json": {
            "errorResponse": {
                "statusCode": 400,
                "status": "Bad Request",
                "messageCode": "XDMP-NOTXN",
                "message": "XDMP-NOTXN: No transaction with identifier 12345",
            },
        },
        "xml": """<error-response xmlns="http://marklogic.com/xdmp/error">
  <status-code>400</status-code>
  <status>Bad Request</status>
  <message-code>XDMP-NOTXN</message-code>
  <message>XDMP-NOTXN: No transaction with identifier 12345</message>
</error-response>""",
    }
    ml_mocker.with_response_body(captures[response_format])
    route = ml_mocker.mock_post()
    controls = {"direction": "descending", "frequency": "fragment", "limit": 0}
    values_controls = controls if len(args) > 1 else {}
    transform_controls = {}
    if transforms:
        transform_controls = {"transform": "missing", "transform_params": {"offset": 0}}

    async with AsyncMLClient() as ml:
        scoped = ml.search(
            database="Other",
            collection=["probe", "other"],
            options=PRICE_OPTIONS,
        )
        operation_method = getattr(scoped, operation)
        with pytest.raises(MarkLogicError, match="XDMP-NOTXN"):
            await operation_method(
                *args,
                pos=[1, 2],
                **values_controls,
                **transform_controls,
                scope=SearchScope(
                    database="Documents",
                    txid="12345",
                    directory="/probe/",
                    timestamp="0",
                    forest_name=["Documents", "Modules"],
                ),
                timeout=2,
            )

    request = route.calls.last.request
    assert dict(request.url.params) == {
        **expected_params,
        "collection": "probe",
        "forest-name": "Documents",
        **({"trans:offset": "0"} if transforms else {}),
    }
    assert request.url.params.get_list("collection") == ["probe", "other"]
    assert request.url.params.get_list("forest-name") == ["Documents", "Modules"]
    assert request.extensions["timeout"] == {
        "connect": 2,
        "read": 2,
        "write": 2,
        "pool": 2,
    }


@pytest.mark.parametrize(
    "additional",
    [
        (
            '<cts:document-query xmlns:cts="http://marklogic.com/cts'
            '"><cts:uri>/probe/a.xml</cts:uri></cts:document-query>'
        ),
        [
            (
                '<cts:document-query xmlns:cts="http://marklogic.com/cts'
                '"><cts:uri>/probe/a.xml</cts:uri></cts:document-query>'
            ),
        ],
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_inline_cts_query_preserves_existing_additional_query(additional):
    options = {**PRICE_OPTIONS, "additional-query": additional}
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price")
    ml_mocker.with_request_body(
        {
            "search": {
                "options": {
                    **PRICE_OPTIONS,
                    "additional-query": [
                        (
                            '<cts:document-query xmlns:cts="http://marklogic.com/cts'
                            '"><cts:uri>/probe/a.xml</cts:uri></cts:document-query>'
                        ),
                        (
                            '<cts:word-query xmlns:cts="http://marklogic.com/cts"><c'
                            "ts:text>zzz</cts:text></cts:word-query>"
                        ),
                    ],
                },
            },
        },
    )
    ml_mocker.with_response_body(
        {"values-response": {"name": "price", "type": "xs:decimal"}},
    )
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        values = await ml.search(options=options).values("price", cts.word_query("zzz"))

    assert values == []
    assert options == {**PRICE_OPTIONS, "additional-query": additional}


@pytest.mark.asyncio
async def test_inline_cts_query_rejects_invalid_additional_query():
    async with AsyncMLClient() as ml:
        with pytest.raises(TypeError) as error:
            await ml.search(options={"additional-query": 1}).values(
                "price",
                cts.word_query("zzz"),
            )

    assert (
        str(error.value)
        == "additional-query must be an XML string or a list of XML strings"
    )
