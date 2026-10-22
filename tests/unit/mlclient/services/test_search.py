from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest
import respx

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.models import JSONDocument, SearchReport, TupleHit, ValueHit, XMLDocument
from mlclient.search.options import Range, opt
from mlclient.search.structured import Element, sq
from mlclient.services import SearchScope, TransactionService
from mlclient.xquery import cts
from tests.utils import data as test_data
from tests.utils import resources as resources_utils
from tests.utils.data import MetadataSpec
from tests.utils.ml_mockers import MLRespXMocker

SEARCH_URL = "http://localhost:8000/v1/search"
VALUES_URL = "http://localhost:8000/v1/values/category"
CTS_QUERY = cts.and_query(
    [cts.collection_query("products"), cts.word_query("coffee")],
)
CTS_BODY = resources_utils.get_test_resource_json(__file__, "cts-body.json")
CTS_XML = resources_utils.read_test_resource_text(__file__, "cts-query.xml")
ERROR_RESPONSE = resources_utils.get_test_resource_json(__file__, "error-response.json")


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_without_scope(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    route = ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(collection="cts-test").documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}

    assert route.call_count == 1


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_with_scope_kwargs(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(collection="cts-test").documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            database="request-db",
            txid="request-tx",
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_inherits_service_scope(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            txid="service-tx",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_scope_kwargs_override_service_scope(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            txid="service-tx",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            database="request-db",
            txid="request-tx",
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_scope_kwargs_clear_service_database(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            txid="service-tx",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            database=None,
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_scope_kwargs_clear_service_transaction(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            txid="service-tx",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            txid=None,
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_operation_scope_overrides_service_scope(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            txid="service-tx",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_scope_kwargs_override_operation_scope(case):
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            txid="service-tx",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_with_transaction_scope_kwargs(case):
    txn = TransactionService(None, "transaction-id", "transaction-db")
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(collection="cts-test").documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            **txn,
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@pytest.mark.parametrize("case", ["matches", "empty"])
@respx.mock
def test_documents_with_report_transaction_scope_inherits_service_database(case):
    txn = TransactionService(None, "transaction-id", None)
    body = resources_utils.read_test_resource_bytes(
        __file__,
        f"documents-report-{case}.bin",
    )
    headers = resources_utils.get_test_resource_json(
        __file__,
        f"documents-report-{case}-headers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(
        {"search": {"qtext": "" if case == "matches" else "missing-value"}},
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type(headers["content-type"])
    ml_mocker.with_response_header("ML-Effective-Timestamp", "123")
    ml_mocker.with_response_body(body)
    ml_mocker.with_request_param("start", "1")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("collection", "cts-test")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report, docs = ml.search(
            database="service-db",
            collection="cts-test",
        ).documents_with_report(
            "" if case == "matches" else "missing-value",
            pos=[1, 2],
            **txn,
        )

    assert isinstance(report, SearchReport)
    assert report.total == (3 if case == "matches" else 0)
    assert report.start == 1
    assert report.page_length == 2
    assert report.effective_timestamp == "123"
    assert [doc.uri for doc in docs] == [item["uri"] for item in report.results]
    assert len(docs) == (2 if case == "matches" else 0)
    if case == "matches":
        assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
        assert docs[1].content == {"active": True, "label": "gamma"}


@respx.mock
def test_documents_for_cts_query():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.xml_doc_body_part("/products/coffee.xml"),
    )
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(CTS_BODY)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents(CTS_QUERY)

    assert [type(doc) for doc in docs] == [XMLDocument, JSONDocument]
    assert [doc.uri for doc in docs] == [
        "/products/coffee.xml",
        "/products/coffee.json",
    ]
    assert docs[1].content == {"root": {"child": "data"}}


@respx.mock
def test_documents_for_structured_query():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-for-structured-query-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents(
            sq.term("coffee"),
        )

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_for_string_query():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-for-string-query-request.json",
        ),
    )
    route = ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents("coffee AND tea")

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]
    assert "structuredQuery" not in route.calls.last.request.url.params


@respx.mock
def test_documents_without_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents()

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_with_scope_kwargs():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents(database="request-db", txid="request-tx")

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_inherits_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db", txid="service-tx").documents()

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_scope_kwargs_override_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db", txid="service-tx").documents(
            database="request-db",
            txid="request-tx",
        )

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_scope_kwargs_clear_service_database():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db", txid="service-tx").documents(
            database=None,
        )

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_scope_kwargs_clear_service_transaction():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db", txid="service-tx").documents(txid=None)

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_operation_scope_overrides_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db", txid="service-tx").documents(
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_scope_kwargs_override_operation_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db", txid="service-tx").documents(
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_with_transaction_scope_kwargs():
    txn = TransactionService(None, "transaction-id", "transaction-db")
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents(**txn)

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_transaction_scope_inherits_service_database():
    txn = TransactionService(None, "transaction-id", None)
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-query-request.json",
        ),
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search(database="service-db").documents(**txn)

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_at_single_position():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "3")
    ml_mocker.with_request_param("pageLength", "1")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-at-single-position-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents("coffee", pos=3)

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_in_position_range():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "11")
    ml_mocker.with_request_param("pageLength", "10")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-in-position-range-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents("coffee", pos=(11, 20))

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_with_metadata():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
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
        resources_utils.get_test_resource_json(
            __file__,
            "documents-with-metadata-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents("coffee", category=["content", "collections"])

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]
    assert docs[0].content == {"root": {"child": "data"}}
    assert docs[0].metadata.collections() == ["products"]


@respx.mock
def test_documents_forwards_options_database_and_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("txid", "12345")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            ("documents-forwards-options-database-and-transaction-request.json"),
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        scoped = ml.search(
            database="Documents",
            txid="12345",
            options="product-options",
        )
        docs = scoped.documents("coffee")

    assert [doc.uri for doc in docs] == ["/products/coffee.json"]


@respx.mock
def test_documents_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("vnd.marklogic.result-estimate", "0")
    ml_mocker.with_empty_response_body()
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-without-matches-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        docs = ml.search.documents("zzz")

    assert docs == []


@respx.mock
def test_documents_with_report_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body({"search": {"qtext": "coffee"}})
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(ERROR_RESPONSE)
    route = ml_mocker.mock_post()

    with MLClient() as ml, pytest.raises(MarkLogicError) as error:
        ml.search.documents_with_report("coffee")

    assert str(error.value) == (
        "[400 Bad Request] (REST-INVALIDPARAM) REST-INVALIDPARAM: Invalid parameter"
    )
    assert route.call_count == 1


@respx.mock
def test_documents_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ERROR_RESPONSE)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "documents-error-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml, pytest.raises(MarkLogicError) as error:
        ml.search.documents("coffee")

    assert "REST-INVALIDPARAM" in str(error.value)


@respx.mock
def test_uris_without_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search.uris(CTS_QUERY, pos=[2, 3])

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_with_scope_kwargs():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search.uris(
            CTS_QUERY,
            pos=[2, 3],
            database="request-db",
            txid="request-tx",
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_inherits_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db", txid="service-tx").uris(
            CTS_QUERY,
            pos=[2, 3],
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_scope_kwargs_override_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db", txid="service-tx").uris(
            CTS_QUERY,
            pos=[2, 3],
            database="request-db",
            txid="request-tx",
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_scope_kwargs_clear_service_database():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db", txid="service-tx").uris(
            CTS_QUERY,
            pos=[2, 3],
            database=None,
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_scope_kwargs_clear_service_transaction():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db", txid="service-tx").uris(
            CTS_QUERY,
            pos=[2, 3],
            txid=None,
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_operation_scope_overrides_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db", txid="service-tx").uris(
            CTS_QUERY,
            pos=[2, 3],
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_scope_kwargs_override_operation_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db", txid="service-tx").uris(
            CTS_QUERY,
            pos=[2, 3],
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_with_transaction_scope_kwargs():
    txn = TransactionService(None, "transaction-id", "transaction-db")
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search.uris(CTS_QUERY, pos=[2, 3], **txn)

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_transaction_scope_inherits_service_database():
    txn = TransactionService(None, "transaction-id", None)
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("start", "2")
    ml_mocker.with_request_param("pageLength", "2")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search(database="service-db").uris(CTS_QUERY, pos=[2, 3], **txn)

    assert uris == ["/products/coffee.xml", "/products/coffee.json"]


@respx.mock
def test_uris_of_single_match():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
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
        resources_utils.get_test_resource_json(
            __file__,
            "uris-of-single-match-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search.uris("coffee")

    assert uris == ["/products/coffee.json"]


@respx.mock
def test_uris_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "uris-without-matches-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        uris = ml.search.uris("zzz")

    assert uris == []


@respx.mock
def test_uris_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(SEARCH_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("category", "quality")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ERROR_RESPONSE)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "uris-error-request.json"),
    )
    ml_mocker.mock_post()

    with MLClient() as ml, pytest.raises(MarkLogicError) as error:
        ml.search.uris()

    assert "REST-INVALIDPARAM" in str(error.value)


@respx.mock
def test_values_without_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(options="product-options").values("category", CTS_QUERY)

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_with_scope_kwargs():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(options="product-options").values(
            "category",
            CTS_QUERY,
            database="request-db",
            txid="request-tx",
        )

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_inherits_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(
            database="service-db",
            txid="service-tx",
            options="product-options",
        ).values("category", CTS_QUERY)

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_scope_kwargs_override_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(
            database="service-db",
            txid="service-tx",
            options="product-options",
        ).values("category", CTS_QUERY, database="request-db", txid="request-tx")

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_scope_kwargs_clear_service_database():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(
            database="service-db",
            txid="service-tx",
            options="product-options",
        ).values("category", CTS_QUERY, database=None)

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_scope_kwargs_clear_service_transaction():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(
            database="service-db",
            txid="service-tx",
            options="product-options",
        ).values("category", CTS_QUERY, txid=None)

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_operation_scope_overrides_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(
            database="service-db",
            txid="service-tx",
            options="product-options",
        ).values(
            "category",
            CTS_QUERY,
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_scope_kwargs_override_operation_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(
            database="service-db",
            txid="service-tx",
            options="product-options",
        ).values(
            "category",
            CTS_QUERY,
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_with_transaction_scope_kwargs():
    txn = TransactionService(None, "transaction-id", "transaction-db")
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(options="product-options").values(
            "category",
            CTS_QUERY,
            **txn,
        )

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


@respx.mock
def test_values_transaction_scope_inherits_service_database():
    txn = TransactionService(None, "transaction-id", None)
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(database="service-db", options="product-options").values(
            "category",
            CTS_QUERY,
            **txn,
        )

    assert values == [ValueHit("drinks", frequency=2), ValueHit("food", frequency=1)]


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
@respx.mock
def test_values_are_converted_from_their_type(atomic_type, lexical, expected):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
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
        resources_utils.get_test_resource_json(
            __file__,
            "values-are-converted-from-their-type-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search.values("category", "coffee", pos=1)

    assert values == [ValueHit(expected, frequency=3)]
    assert type(values[0].value) is type(expected)


@respx.mock
def test_values_without_matches():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("txid", "12345")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {"values-response": {"name": "category", "type": "xs:string"}},
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "values-without-matches-request.json",
        ),
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        values = ml.search(database="Documents", txid="12345").values("category")

    assert values == []


@respx.mock
def test_values_reject_tuples():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {"values-response": {"name": "category", "tuple": [{"frequency": 1}]}},
    )
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "values-reject-tuples-request.json",
        ),
    )
    ml_mocker.mock_post()

    with (
        MLClient() as ml,
        pytest.raises(ValueError, match=r"use tuples\(\)") as error,
    ):
        ml.search.values("category")

    assert str(error.value) == (
        "values() reads values definitions; use tuples() for co-occurrences"
    )


@respx.mock
def test_values_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(ERROR_RESPONSE)
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(__file__, "values-error-request.json"),
    )
    ml_mocker.mock_post()

    with MLClient() as ml, pytest.raises(MarkLogicError) as error:
        ml.search.values("category")

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
@respx.mock
def test_invalid_pos_is_rejected_before_request(pos, error_type, message):

    with MLClient() as ml, pytest.raises(error_type) as error:
        ml.search.documents("coffee", pos=pos)

    assert str(error.value) == message


@respx.mock
def test_invalid_query_is_rejected_before_request():

    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.uris({"q": "coffee"})

    assert str(error.value) == (
        "query dictionary must contain exactly one search, query or ctsquery dictionary"
    )


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


@pytest.mark.parametrize("aggregate_path", [None, ""])
@pytest.mark.parametrize(
    "case",
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
@respx.mock
def test_aggregate_native_result(case, aggregate_path):
    name, scalar_type, function, lexical, expected = case
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
    ml_mocker.with_request_param("aggregatePath", aggregate_path)
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

    with MLClient() as ml:
        result = ml.search(options=options).aggregate(
            name,
            function,
            aggregate_path=aggregate_path,
        )

    assert result == expected
    assert type(result) is type(expected)


# Synthetic plugin results verify that lexicon types do not coerce plugin output.
@pytest.mark.parametrize(
    "payload",
    [
        {"name": "customAverage", "_value": 2.5},
        {"name": "customAverage", "_value": "2.5"},
        {"name": "customAverage", "_value": {"average": 2.5}},
        {"name": "customAverage", "_value": [2, 3]},
        {"name": "customAverage", "_value": None},
        {"name": "customAverage"},
    ],
)
@respx.mock
def test_plugin_aggregate_preserves_json_value(payload):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("aggregate", "customAverage")
    ml_mocker.with_request_param("aggregatePath", "/native/statistics")
    ml_mocker.with_request_body({"search": {"qtext": "coffee"}})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(
        {
            "values-response": {
                "type": "xs:int",
                "aggregate-result": [payload],
            },
        },
    )
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search.aggregate(
            "category",
            "customAverage",
            "coffee",
            aggregate_path="/native/statistics",
        )

    assert result == payload.get("_value")
    assert type(result) is type(payload.get("_value"))


@respx.mock
def test_plugin_aggregate_preserves_native_map():
    payload = resources_utils.get_test_resource_json(
        __file__,
        "native-plugin-map-response.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values/amount")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("aggregate", "variance")
    ml_mocker.with_request_param("aggregatePath", "native/sampleplugin")
    ml_mocker.with_request_body({"search": {}})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(payload)
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search.aggregate(
            "amount",
            "variance",
            aggregate_path="native/sampleplugin",
        )

    assert result == {
        "entry": {
            "key": "variance",
            "value": {
                "type": "xs:double",
                "_value": 0.25,
            },
        },
    }
    assert type(result) is dict


@respx.mock
def test_aggregate_without_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(options=PRICE_OPTIONS).aggregate("price", "avg", "zzz")

    assert result is None


@respx.mock
def test_aggregate_with_scope_kwargs():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(options=PRICE_OPTIONS).aggregate(
            "price",
            "avg",
            "zzz",
            database="request-db",
            txid="request-tx",
        )

    assert result is None


@respx.mock
def test_aggregate_inherits_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(
            database="service-db",
            txid="service-tx",
            options=PRICE_OPTIONS,
        ).aggregate("price", "avg", "zzz")

    assert result is None


@respx.mock
def test_aggregate_scope_kwargs_override_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(
            database="service-db",
            txid="service-tx",
            options=PRICE_OPTIONS,
        ).aggregate("price", "avg", "zzz", database="request-db", txid="request-tx")

    assert result is None


@respx.mock
def test_aggregate_scope_kwargs_clear_service_database():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(
            database="service-db",
            txid="service-tx",
            options=PRICE_OPTIONS,
        ).aggregate("price", "avg", "zzz", database=None)

    assert result is None


@respx.mock
def test_aggregate_scope_kwargs_clear_service_transaction():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(
            database="service-db",
            txid="service-tx",
            options=PRICE_OPTIONS,
        ).aggregate("price", "avg", "zzz", txid=None)

    assert result is None


@respx.mock
def test_aggregate_operation_scope_overrides_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(
            database="service-db",
            txid="service-tx",
            options=PRICE_OPTIONS,
        ).aggregate(
            "price",
            "avg",
            "zzz",
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

    assert result is None


@respx.mock
def test_aggregate_scope_kwargs_override_operation_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(
            database="service-db",
            txid="service-tx",
            options=PRICE_OPTIONS,
        ).aggregate(
            "price",
            "avg",
            "zzz",
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

    assert result is None


@respx.mock
def test_aggregate_with_transaction_scope_kwargs():
    txn = TransactionService(None, "transaction-id", "transaction-db")
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(options=PRICE_OPTIONS).aggregate(
            "price",
            "avg",
            "zzz",
            **txn,
        )

    assert result is None


@respx.mock
def test_aggregate_transaction_scope_inherits_service_database():
    txn = TransactionService(None, "transaction-id", None)
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
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
    ml_mocker.with_request_param("view", "aggregate")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("aggregate", "avg")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        result = ml.search(database="service-db", options=PRICE_OPTIONS).aggregate(
            "price",
            "avg",
            "zzz",
            **txn,
        )

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
@respx.mock
def test_inline_options_with_query(query, fragment):
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

    with MLClient() as ml:
        assert ml.search(options=PRICE_OPTIONS).values("price", query) == []


@respx.mock
def test_values_with_options_builder_and_controls():
    options = opt.options(opt.values("price", Range(Element("price"), "xs:decimal")))
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

    with MLClient() as ml:
        values = ml.search(options=options).values(
            "price",
            direction="descending",
            frequency="fragment",
            limit=1,
        )

    assert values == [ValueHit(Decimal("2.5"), frequency=1)]


def test_invalid_options():

    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search(options=123).values("price")

    assert str(error.value) == (
        "options must be an installed name, inline dictionary or SearchOptions, got int"
    )


@pytest.mark.parametrize("options", [None, "product-options", PRICE_OPTIONS])
def test_invalid_query_is_rejected_for_get_and_combined_queries(options):

    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search(options=options).uris(42)

    assert str(error.value) == (
        "query must be a SearchQuery, a query dictionary, a string query or None"
    )


@respx.mock
def test_tuples_without_scope():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(options=options).tuples("price-day")

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_with_scope_kwargs():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(options=options).tuples(
            "price-day",
            database="request-db",
            txid="request-tx",
        )

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_inherits_service_scope():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(
            database="service-db",
            txid="service-tx",
            options=options,
        ).tuples("price-day")

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_scope_kwargs_override_service_scope():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(
            database="service-db",
            txid="service-tx",
            options=options,
        ).tuples("price-day", database="request-db", txid="request-tx")

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_scope_kwargs_clear_service_database():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(
            database="service-db",
            txid="service-tx",
            options=options,
        ).tuples("price-day", database=None)

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_scope_kwargs_clear_service_transaction():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(
            database="service-db",
            txid="service-tx",
            options=options,
        ).tuples("price-day", txid=None)

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_operation_scope_overrides_service_scope():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(
            database="service-db",
            txid="service-tx",
            options=options,
        ).tuples(
            "price-day",
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_scope_kwargs_override_operation_scope():
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(
            database="service-db",
            txid="service-tx",
            options=options,
        ).tuples(
            "price-day",
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_with_transaction_scope_kwargs():
    txn = TransactionService(None, "transaction-id", "transaction-db")
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(options=options).tuples("price-day", **txn)

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_transaction_scope_inherits_service_database():
    txn = TransactionService(None, "transaction-id", None)
    options = opt.options(
        opt.tuples(
            "price-day",
            Range(Element("price"), "xs:decimal"),
            Range(Element("day"), "xs:date"),
        ),
    )
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(VALUES_URL)
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_url("http://localhost:8000/v1/values/price-day")
    ml_mocker.with_request_header("Accept", "application/xml")
    ml_mocker.with_request_body(
        resources_utils.get_test_resource_json(
            __file__,
            "tuples-have-individual-types-request.json",
        ),
    )
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        """<search:values-response name="price-day"
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
</search:values-response>""",
    )
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(database="service-db", options=options).tuples(
            "price-day",
            **txn,
        )

    assert tuples == [
        TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
        TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
    ]


@respx.mock
def test_tuples_keep_an_empty_string_value():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values/pairs")
    ml_mocker.with_request_param("options", "pair-options")
    ml_mocker.with_request_body({"search": {}})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(
        resources_utils.read_test_resource_bytes(__file__, "tuples-empty-string.xml"),
    )
    ml_mocker.with_request_param("format", "xml")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.mock_post()

    with MLClient() as ml:
        tuples = ml.search(options="pair-options").tuples("pairs")

    assert tuples == [TupleHit(("", 3), frequency=2)]


@respx.mock
def test_tuples_reject_values_definition():
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

    with (
        MLClient() as ml,
        pytest.raises(ValueError, match="tuples definitions") as error,
    ):
        ml.search(options=PRICE_OPTIONS).tuples("price")

    assert str(error.value) == (
        "tuples() reads tuples definitions; use values() for single values"
    )


@respx.mock
def test_report_without_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search.report("product")

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


@respx.mock
def test_report_with_scope_kwargs():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search.report("product", database="request-db", txid="request-tx")

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


@respx.mock
def test_report_inherits_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db", txid="service-tx").report("product")

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


@respx.mock
def test_report_scope_kwargs_override_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db", txid="service-tx").report(
            "product",
            database="request-db",
            txid="request-tx",
        )

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


@respx.mock
def test_report_scope_kwargs_clear_service_database():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("txid", "service-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db", txid="service-tx").report(
            "product",
            database=None,
        )

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


@respx.mock
def test_report_scope_kwargs_clear_service_transaction():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db", txid="service-tx").report(
            "product",
            txid=None,
        )

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


@respx.mock
def test_report_operation_scope_overrides_service_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "operation-db")
    ml_mocker.with_request_param("txid", "operation-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db", txid="service-tx").report(
            "product",
            scope=SearchScope(database="operation-db", txid="operation-tx"),
        )

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


@respx.mock
def test_report_scope_kwargs_override_operation_scope():
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "request-db")
    ml_mocker.with_request_param("txid", "request-tx")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db", txid="service-tx").report(
            "product",
            scope=SearchScope(database="operation-db", txid="operation-tx"),
            database="request-db",
            txid="request-tx",
        )

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


@respx.mock
def test_report_with_transaction_scope_kwargs():
    txn = TransactionService(None, "transaction-id", "transaction-db")
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "transaction-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search.report("product", **txn)

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


@respx.mock
def test_report_transaction_scope_inherits_service_database():
    txn = TransactionService(None, "transaction-id", None)
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url(SEARCH_URL)
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
        resources_utils.get_test_resource_json(
            __file__,
            "report-retains-empty-native-report-and-timestamp-request.json",
        ),
    )
    ml_mocker.with_request_param("view", "all")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "service-db")
    ml_mocker.with_request_param("txid", "transaction-id")
    ml_mocker.mock_post()

    with MLClient() as ml:
        report = ml.search(database="service-db").report("product", **txn)

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
@respx.mock
def test_operation_forwards_all_controls_and_transaction_error(
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

    with MLClient() as ml:
        scoped = ml.search(
            database="Other",
            collection=["probe", "other"],
            options=PRICE_OPTIONS,
        )
        operation_method = getattr(scoped, operation)
        with pytest.raises(MarkLogicError, match="XDMP-NOTXN"):
            operation_method(
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
@respx.mock
def test_inline_cts_query_preserves_existing_additional_query(additional):
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

    with MLClient() as ml:
        values = ml.search(options=options).values("price", cts.word_query("zzz"))

    assert values == []
    assert options == {**PRICE_OPTIONS, "additional-query": additional}


def test_inline_cts_query_rejects_invalid_additional_query():

    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search(options={"additional-query": 1}).values(
            "price",
            cts.word_query("zzz"),
        )

    assert (
        str(error.value)
        == "additional-query must be an XML string or a list of XML strings"
    )


@pytest.mark.parametrize(
    "query",
    [sq.term("blue"), cts.word_query("blue")],
    ids=["structured", "cts"],
)
@respx.mock
def test_search_sends_combined_query_with_scope_defaults(query):
    combined = query.to_combined_query(options={"page-length": 3}, qtext="coffee")
    expected = deepcopy(combined)
    expected["search"]["options"]["return-facets"] = False
    before = deepcopy(combined)
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("pageLength", "3")
    ml_mocker.with_request_header("Content-Type", "application/json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(expected)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()
    with MLClient() as ml:
        result = ml.search(
            options={"page-length": 8, "return-facets": False},
        ).documents(combined)
    assert result == []
    assert combined == before


@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            {"unsupported": {}},
            (
                "query dictionary must contain exactly one "
                "search, query or ctsquery dictionary"
            ),
        ),
        (
            {"search": []},
            (
                "query dictionary must contain exactly one "
                "search, query or ctsquery dictionary"
            ),
        ),
        (
            {"search": {}, "qtext": "coffee"},
            (
                "query dictionary must contain exactly one "
                "search, query or ctsquery dictionary"
            ),
        ),
        (
            {"search": {"options": "catalog"}},
            "combined query options must be a dictionary",
        ),
    ],
    ids=["unknown-root", "non-dict-search", "outer-qtext", "non-dict-options"],
)
def test_search_rejects_invalid_combined_query(query, message):
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.documents(query)
    assert str(error.value) == message


@pytest.mark.parametrize(
    "query",
    [
        {"ctsquery": {"wordQuery": {"text": "blue"}}},
        cts.word_query("blue").to_combined_query(qtext="coffee"),
    ],
    ids=["cts-json", "combined-json"],
)
def test_values_rejects_raw_cts_json(query):
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.values("price", query)
    assert str(error.value) == (
        "raw CTS JSON cannot filter lexicon operations; pass a CTS query object instead"
    )


@respx.mock
def test_values_sends_combined_structured_query():
    options = {"values": [{"name": "uris", "uri": {}}]}
    combined = sq.term("blue").to_combined_query(options=options, qtext="coffee")
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url("http://localhost:8000/v1/values/uris")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "values")
    ml_mocker.with_request_header("Content-Type", "application/json")
    ml_mocker.with_request_header("Accept", "application/json")
    ml_mocker.with_request_body(combined)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(
        {"values-response": {"name": "uris", "type": "xs:string"}},
    )
    ml_mocker.mock_post()
    with MLClient() as ml:
        assert ml.search.values("uris", combined) == []


@pytest.mark.parametrize(
    ("override", "expected_options", "url_options", "page_length"),
    [
        ({"page-length": 2}, {"page-length": 2, "return-facets": False}, None, "2"),
        (
            opt.options(opt.word_constraint("title", Element("title"))),
            {
                "page-length": 3,
                "return-facets": False,
                "constraint": [
                    {"name": "title", "word": {"element": {"name": "title", "ns": ""}}},
                ],
            },
            None,
            "3",
        ),
        (None, None, None, None),
        ("request-options", {"page-length": 3}, "request-options", "3"),
    ],
    ids=["inline", "builder", "clear", "installed"],
)
@respx.mock
def test_request_scope_options_override_combined_query_and_service(
    override,
    expected_options,
    url_options,
    page_length,
):
    combined = sq.term("blue").to_combined_query(options={"page-length": 3})
    expected = {"search": {"query": {"queries": [{"term-query": {"text": ["blue"]}}]}}}
    if expected_options is not None:
        expected["search"]["options"] = expected_options
    params = {"format": "json"}
    if page_length is not None:
        params["pageLength"] = page_length
    if url_options is not None:
        params["options"] = url_options
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    for name, value in params.items():
        ml_mocker.with_request_param(name, value)
    ml_mocker.with_request_body(expected)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as ml:
        documents = ml.search(
            options={"page-length": 8, "return-facets": False},
        ).documents(
            combined,
            scope=SearchScope(options=override),
        )

    assert documents == []


@pytest.mark.parametrize(
    "query",
    [
        {"query": {"term-query": {"text": "blue"}}},
        {"ctsquery": {"wordQuery": {"text": "blue"}}},
    ],
    ids=["structured-json", "cts-json"],
)
@respx.mock
def test_search_accepts_raw_query_json_with_scope_options(query):
    before = deepcopy(query)
    expected = {"search": {**query, "options": {"page-length": 5}}}
    ml_mocker = MLRespXMocker(use_router=False, strict_params=True)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("pageLength", "5")
    ml_mocker.with_request_header("Content-Type", "application/json")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_request_body(expected)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as ml:
        documents = ml.search(options={"page-length": 5}).documents(query)

    assert documents == []
    assert query == before


@pytest.mark.parametrize("query", [{"query": []}, {"ctsquery": []}, {}])
def test_search_rejects_invalid_raw_query_json(query):
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.documents(query)
    assert str(error.value) == (
        "query dictionary must contain exactly one search, query or ctsquery dictionary"
    )
