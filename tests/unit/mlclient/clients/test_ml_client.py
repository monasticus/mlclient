from pathlib import Path

import httpx
import respx

from mlclient import MLClient
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


def test_connection():
    client = MLClient()
    assert not client.is_connected()

    client.connect()
    assert client.is_connected()

    client.disconnect()
    assert not client.is_connected()


def test_context_mng():
    with MLClient() as client:
        assert client.is_connected()

    assert not client.is_connected()


@respx.mock
def test_request_when_disconnected():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-response.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    client = MLClient()

    assert not client.is_connected()
    resp = client.get("/manage/v2/servers")
    assert not client.is_connected()
    assert resp.status_code == httpx.codes.OK
    assert resp.content == Path(response_body_path).read_bytes()
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"

    # This assertion works only from the clients package level.
    # It should be uncommented once the following bug is addressed:
    # https://github.com/pytest-dev/pytest/issues/7335
    #
    # assert (
    #     "MLClient is not connected -- "
    #     "A request will be sent in an ad-hoc initialized session "
    #     "(GET /manage/v2/servers)"
    # ) in caplog.text


@respx.mock
def test_get():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-response.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    with MLClient() as client:
        resp = client.get("/manage/v2/servers")
    assert resp.status_code == httpx.codes.OK
    assert resp.content == Path(response_body_path).read_bytes()
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_get_with_customized_params_and_headers():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-with-customized-params-response.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("custom-header", "custom-value")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    with MLClient() as client:
        resp = client.get(
            "/manage/v2/servers",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == Path(response_body_path).read_bytes()
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_post():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-response.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_post()

    with MLClient() as client:
        resp = client.post("/manage/v2/databases/Documents")
    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.content == Path(response_body_path).read_bytes()
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_post_with_customized_params_and_headers_and_body_different_than_json():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": "()"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as client:
        resp = client.post(
            "/v1/eval",
            body={"xquery": "()"},
            params={"database": "Documents"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""


@respx.mock
def test_post_with_customized_params_and_headers_and_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"operation": "clear-database"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.mock_post()

    with MLClient() as client:
        resp = client.post(
            "/manage/v2/databases/Documents",
            body={"operation": "clear-database"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""
    assert resp.headers.get("Content-Type") == "application/json; charset=UTF-8"


@respx.mock
def test_put():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-response.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_put()

    with MLClient() as client:
        resp = client.put("/v1/documents")
    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.content == Path(response_body_path).read_bytes()
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_put_with_customized_params_and_headers_and_body_different_than_json():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("uri", "/doc.xml")
    ml_mocker.with_request_content_type("application/xml")
    ml_mocker.with_request_body("<document/>")
    ml_mocker.with_response_code(201)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    with MLClient() as client:
        resp = client.put(
            "/v1/documents",
            body="<document/>",
            params={"database": "Documents", "uri": "/doc.xml"},
            headers={"Content-Type": "application/xml"},
        )
    assert resp.status_code == httpx.codes.CREATED
    assert resp.content == b""


@respx.mock
def test_put_with_customized_params_and_headers_and_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("uri", "/doc.json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"document": {}})
    ml_mocker.with_response_code(201)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    with MLClient() as client:
        resp = client.put(
            "/v1/documents",
            body={"document": {}},
            params={"database": "Documents", "uri": "/doc.json"},
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == httpx.codes.CREATED
    assert resp.content == b""


@respx.mock
def test_delete():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    with MLClient() as client:
        resp = client.delete_("/manage/v2/databases/custom-db")
    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@respx.mock
def test_delete_with_customized_params_and_headers():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("custom-header", "custom-value")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    with MLClient() as client:
        resp = client.delete_(
            "/manage/v2/databases/custom-db",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )
    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""
