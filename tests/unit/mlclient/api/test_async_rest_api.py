import httpx
import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import WrongParametersError
from mlclient.calls import EvalCall
from mlclient.models import DocumentsBodyPart
from tests.utils import data as test_data, resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


STRUCTURED_QUERY = resources_utils.read_test_resource_text(
    __file__,
    "structured-query.txt",
)
COMBINED_QUERY = resources_utils.get_test_resource_json(__file__, "combined-query.json")
URIS_VALUES_QUERY = resources_utils.get_test_resource_json(
    __file__,
    "uris-values-query.json",
)
URIS_VALUES_RESPONSE = resources_utils.get_test_resource_json(
    __file__,
    "uris-values-response.json",
)
VALUES_ERROR = resources_utils.get_test_resource_json(__file__, "values-error.json")


@pytest.mark.asyncio
@respx.mock
async def test_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": "1+1"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("xs:integer", "2")
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.call(EvalCall(xquery="1+1"))

    assert resp.status_code == httpx.codes.OK


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@pytest.mark.asyncio
@respx.mock
async def test_eval(xquery):
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

    async with AsyncMLClient() as ml:
        resp = await ml.rest.eval.post(
            xquery=xquery,
            variables={"element": "<parent><child/></parent>"},
        )

    assert resp.status_code == httpx.codes.OK
    assert "<new-parent><child/></new-parent>" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_documents():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-get-documents.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_request_param("uri", "/path/to/non-existing/document.xml")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.documents.get(
            uri="/path/to/non-existing/document.xml",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"


@pytest.mark.asyncio
@respx.mock
async def test_post_documents():
    body_part = {
        "content-type": "application/json",
        "content-disposition": "inline",
        "content": {"root": "data"},
    }

    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-post-documents.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.documents.post([DocumentsBodyPart(**body_part)])

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


@pytest.mark.asyncio
@respx.mock
async def test_delete_documents():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-delete-documents.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/documents")
    ml_mocker.with_request_param("uri", "/path/to/non-existing/document.xml")
    ml_mocker.with_request_param("result", "wiped")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.documents.delete(
            uri="/path/to/non-existing/document.xml",
            wipe_temporal=True,
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Endpoint does not support query parameter: "
        "invalid parameters: result "
        "for /path/to/non-existing/document.xml"
    ) in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_create_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions")
    ml_mocker.with_request_param("name", "my-txn")
    ml_mocker.with_response_code(303)
    ml_mocker.with_response_header("Location", "/v1/transactions/12345")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.transactions.create(name="my-txn")

    assert resp.status_code == httpx.codes.SEE_OTHER
    assert resp.headers.get("Location") == "/v1/transactions/12345"


@pytest.mark.asyncio
@respx.mock
async def test_get_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"transaction-status": {"transaction-id": "12345"}})
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.transactions.get("12345", data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["transaction-status"]["transaction-id"] == "12345"


@pytest.mark.asyncio
@respx.mock
async def test_post_transaction():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_request_param("result", "commit")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.transactions.post("12345", result="commit")

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_get_search_documents():
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

    async with AsyncMLClient() as ml:
        resp = await ml.rest.search.get(
            structured_query=STRUCTURED_QUERY,
            page_length=1,
            multipart=True,
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.headers["vnd.marklogic.result-estimate"] == "3"
    assert b'filename="/products/coffee.json"' in resp.content


@pytest.mark.asyncio
@respx.mock
async def test_post_search():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body(COMBINED_QUERY)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"total": 1, "results": [{"uri": "/a.json"}]})
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.search.post(COMBINED_QUERY, data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == {"total": 1, "results": [{"uri": "/a.json"}]}


@pytest.mark.asyncio
@respx.mock
async def test_delete_search():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_request_param("collection", "products")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.search.delete(collection="products")

    assert resp.status_code == httpx.codes.NO_CONTENT


@pytest.mark.asyncio
@respx.mock
async def test_delete_search_clearing_database():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.search.delete(database="Documents", clear_database=True)

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert dict(route.calls.last.request.url.params) == {"database": "Documents"}


@pytest.mark.asyncio
@respx.mock
async def test_delete_search_without_filters_is_rejected_before_any_request():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        with pytest.raises(WrongParametersError):
            await ml.rest.search.delete(database="Documents")

    assert not route.called


@pytest.mark.parametrize("name", ["collection", "directory"])
@pytest.mark.parametrize("value", [[], ()])
@pytest.mark.asyncio
@respx.mock
async def test_delete_search_empty_filters_are_rejected_before_any_request(name, value):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/search")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        with pytest.raises(WrongParametersError):
            await ml.rest.search.delete(**{name: value})

    assert not route.called


@pytest.mark.asyncio
@respx.mock
async def test_get_values_list():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(
        {"values-list": {"values": [{"name": "category"}]}},
    )
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.values.get_list(
            data_format="json",
            options="product-options",
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == {"values-list": {"values": [{"name": "category"}]}}


@pytest.mark.asyncio
@respx.mock
async def test_get_values():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values/category")
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(VALUES_ERROR)
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.values.get(
            "category",
            options="product-options",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.json()["errorResponse"]["messageCode"] == "REST-INVALIDPARAM"


@pytest.mark.asyncio
@respx.mock
async def test_get_values_of_a_named_definition():
    body = resources_utils.get_test_resource_json(__file__, "named-values.json")
    url = "http://localhost:8000/v1/values/category"
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(url)
    ml_mocker.with_request_param("options", "product-options")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("limit", "5")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(body)
    route = ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.values.get(
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


@pytest.mark.asyncio
@respx.mock
async def test_post_values():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/values/uris")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body(URIS_VALUES_QUERY)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(URIS_VALUES_RESPONSE)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.rest.values.post("uris", URIS_VALUES_QUERY, data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json() == URIS_VALUES_RESPONSE
