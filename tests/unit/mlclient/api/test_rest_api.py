from pathlib import Path

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.exceptions import WrongParametersError
from mlclient.models import DocumentsBodyPart
from tests.utils import data as test_data, resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


STRUCTURED_QUERY = '{"search": {"ctsquery": {"wordQuery": {"text": ["coffee"]}}}}'
COMBINED_QUERY = {"search": {"ctsquery": {"wordQuery": {"text": ["coffee"]}}}}
URIS_VALUES_QUERY = {"search": {"options": {"values": [{"name": "uris", "uri": None}]}}}
URIS_VALUES_RESPONSE = {
    "values-response": {
        "name": "uris",
        "type": "xs:string",
        "distinct-value": [{"frequency": 1, "_value": "/a.json"}],
    },
}
VALUES_ERROR = {
    "errorResponse": {
        "statusCode": 400,
        "status": "Bad Request",
        "messageCode": "REST-INVALIDPARAM",
        "message": "REST-INVALIDPARAM: (err:FOER0000) Invalid parameter: "
        "No values or tuples specification named: category",
    },
}


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@respx.mock
def test_eval(xquery):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": xquery,
            "vars": '{"element": "<parent><child/></parent>"}',
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("element()", "<new-parent><child/></new-parent>")
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.eval.post(
            xquery=xquery,
            variables={"element": "<parent><child/></parent>"},
        )

    assert resp.status_code == httpx.codes.OK
    assert "<new-parent><child/></new-parent>" in resp.text


@respx.mock
def test_get_documents():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-documents.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_request_param("uri", "/path/to/non-existing/document.xml")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.rest.documents.get(
            uri="/path/to/non-existing/document.xml",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"


@respx.mock
def test_post_documents():
    body_part = {
        "content-type": "application/json",
        "content-disposition": "inline",
        "content": {"root": "data"},
    }

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-documents.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.documents.post([DocumentsBodyPart(**body_part)])

    assert resp.status_code == httpx.codes.INTERNAL_SERVER_ERROR
    assert resp.json() == {
        "errorResponse": {
            "statusCode": "500",
            "status": "Internal Server Error",
            "messageCode": "XDMP-AS",
            "message": "XDMP-AS: (err:XPTY0004) $uri as xs:string -- "
            "Invalid coercion: () as xs:string",
        },
    }


@respx.mock
def test_delete_documents():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-documents.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_request_param("uri", "/path/to/non-existing/document.xml")
    ml_mocker.with_request_param("result", "wiped")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_delete()

    with MLClient() as ml:
        resp = ml.rest.documents.delete(
            uri="/path/to/non-existing/document.xml",
            wipe_temporal=True,
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Endpoint does not support query parameter: "
        "invalid parameters: result "
        "for /path/to/non-existing/document.xml"
    ) in resp.text


@respx.mock
def test_create_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions")
    ml_mocker.with_request_param("name", "my-txn")
    ml_mocker.with_response_code(303)
    ml_mocker.with_response_header("Location", "/v1/transactions/12345")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.transactions.create(name="my-txn")

    assert resp.status_code == httpx.codes.SEE_OTHER
    assert resp.headers.get("Location") == "/v1/transactions/12345"


@respx.mock
def test_get_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"transaction-status": {"transaction-id": "12345"}})
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.rest.transactions.get("12345", data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["transaction-status"]["transaction-id"] == "12345"


@respx.mock
def test_post_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_request_param("result", "commit")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.transactions.post("12345", result="commit")

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@respx.mock
def test_get_search_documents():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("structuredQuery", STRUCTURED_QUERY)
    ml_mocker.with_request_param("pageLength", "1")
    ml_mocker.with_request_header("Accept", "multipart/mixed")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_header("vnd.marklogic.result-estimate", "3")
    ml_mocker.with_response_documents_body_part(
        test_data.json_doc_body_part("/products/coffee.json"),
    )
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.rest.search.get(
            structured_query=STRUCTURED_QUERY,
            page_length=1,
            multipart=True,
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.headers["vnd.marklogic.result-estimate"] == "3"
    assert b'filename="/products/coffee.json"' in resp.content


@respx.mock
def test_post_search():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body(COMBINED_QUERY)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"total": 1, "results": [{"uri": "/a.json"}]})
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.search.post(COMBINED_QUERY, data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == {"total": 1, "results": [{"uri": "/a.json"}]}


@respx.mock
def test_delete_search():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("collection", "products")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    with MLClient() as ml:
        resp = ml.rest.search.delete(collection="products")

    assert resp.status_code == httpx.codes.NO_CONTENT


@respx.mock
def test_delete_search_clearing_database():
    route = respx.delete("http://localhost:8000/v1/search").respond(204)

    with MLClient() as ml:
        resp = ml.rest.search.delete(database="Documents", clear_database=True)

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert dict(route.calls.last.request.url.params) == {"database": "Documents"}


@respx.mock
def test_delete_search_without_filters_is_rejected_before_any_request():
    route = respx.delete("http://localhost:8000/v1/search").respond(204)

    with MLClient() as ml, pytest.raises(WrongParametersError):
        ml.rest.search.delete(database="Documents")

    assert not route.called


@pytest.mark.parametrize("name", ["collection", "directory"])
@pytest.mark.parametrize("value", [[], ()])
@respx.mock
def test_delete_search_empty_filters_are_rejected_before_any_request(name, value):
    route = respx.delete("http://localhost:8000/v1/search").respond(204)

    with MLClient() as ml, pytest.raises(WrongParametersError):
        ml.rest.search.delete(**{name: value})

    assert not route.called


@respx.mock
def test_get_values_list():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(
        {"values-list": {"values": [{"name": "category"}]}},
    )
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.rest.values.get_list(
            data_format="json",
            options="product-options",
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == {"values-list": {"values": [{"name": "category"}]}}


@respx.mock
def test_get_values():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values/category")
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(VALUES_ERROR)
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.rest.values.get(
            "category",
            options="product-options",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.json()["errorResponse"]["messageCode"] == "REST-INVALIDPARAM"


@respx.mock
def test_get_values_of_a_named_definition():
    body = {
        "values-response": {
            "name": "category",
            "type": "xs:string",
            "distinct-value": [{"frequency": 2, "_value": "drinks"}],
        },
    }
    url = "http://localhost:8000/v1/values/category"
    route = respx.get(url).respond(200, json=body)

    with MLClient() as ml:
        resp = ml.rest.values.get(
            "category",
            options="product-options",
            data_format="json",
            limit=5,
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == body
    request = route.calls.last.request
    assert dict(request.url.params) == {
        "options": "product-options",
        "format": "json",
        "limit": "5",
    }
    assert request.headers["Accept"] == "application/json"


@respx.mock
def test_post_values():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values/uris")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body(URIS_VALUES_QUERY)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(URIS_VALUES_RESPONSE)
    ml_mocker.mock_post()

    with MLClient() as ml:
        resp = ml.rest.values.post("uris", URIS_VALUES_QUERY, data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == URIS_VALUES_RESPONSE
