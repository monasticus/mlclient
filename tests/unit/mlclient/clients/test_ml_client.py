from pathlib import Path

import responses

from mlclient import MLClient
from tests import tools
from tests.tools import MLResponseBuilder


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


def test_request_when_disconnected():
    client = MLClient()
    resp = client.get("/manage/v2/servers")

    assert resp is None


@responses.activate
def test_get():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/servers")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(200)
    response_body_path = tools.get_test_resource_path(__file__, "test-get-response.xml")
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLClient(auth_method="digest") as client:
        resp = client.get("/manage/v2/servers")

    assert resp.request.method == "GET"
    assert "?" not in resp.request.url
    assert resp.status_code == 200


@responses.activate
def test_get_with_customized_params_and_headers():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/servers")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    response_body_path = tools.get_test_resource_path(
        __file__,
        "test-get-with-customized-params-response.json",
    )
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLClient(auth_method="digest") as client:
        resp = client.get(
            "/manage/v2/servers",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )

    assert resp.request.method == "GET"
    assert "?format=json" in resp.request.url
    assert "custom-header" in resp.request.headers
    assert resp.request.headers["custom-header"] == "custom-value"
    assert resp.status_code == 200


@responses.activate
def test_post():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases/Documents")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    response_body_path = tools.get_test_resource_path(
        __file__,
        "test-post-response.xml",
    )
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLClient(auth_method="digest") as client:
        resp = client.post("/manage/v2/databases/Documents")

    assert resp.request.method == "POST"
    assert "?" not in resp.request.url
    assert resp.request.body is None
    assert resp.status_code == 400


@responses.activate
def test_post_with_customized_params_and_headers_and_body_different_than_json():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_param("database", "Documents")
    builder.with_request_body({"xquery": "()"})
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    with MLClient(auth_method="digest") as client:
        resp = client.post(
            "/v1/eval",
            body={"xquery": "()"},
            params={"database": "Documents"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert resp.request.method == "POST"
    assert "?database=Documents" in resp.request.url
    assert "Content-Type" in resp.request.headers
    assert resp.request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert resp.request.body == "xquery=%28%29"
    assert resp.status_code == 200


@responses.activate
def test_post_with_customized_params_and_headers_and_json_body():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases/Documents")
    builder.with_request_content_type("application/json")
    builder.with_request_param("format", "json")
    builder.with_request_body({"operation": "clear-database"})
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_empty_response_body()
    builder.build_post()

    with MLClient(auth_method="digest") as client:
        resp = client.post(
            "/manage/v2/databases/Documents",
            body={"operation": "clear-database"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.request.method == "POST"
    assert "?format=json" in resp.request.url
    assert "Content-Type" in resp.request.headers
    assert resp.request.headers["Content-Type"] == "application/json"
    assert resp.request.body == b'{"operation": "clear-database"}'
    assert resp.status_code == 200


@responses.activate
def test_put():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    response_body_path = tools.get_test_resource_path(__file__, "test-put-response.xml")
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLClient(auth_method="digest") as client:
        resp = client.put("/v1/documents")

    assert resp.request.method == "PUT"
    assert "?" not in resp.request.url
    assert resp.request.body is None
    assert resp.status_code == 400


@responses.activate
def test_put_with_customized_params_and_headers_and_body_different_than_json():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_content_type("application/xml")
    builder.with_request_param("database", "Documents")
    builder.with_request_param("uri", "/doc.xml")
    builder.with_response_status(201)
    builder.with_empty_response_body()
    builder.build_put()

    with MLClient(auth_method="digest") as client:
        resp = client.put(
            "/v1/documents",
            body="<document/>",
            params={"database": "Documents", "uri": "/doc.xml"},
            headers={"Content-Type": "application/xml"},
        )

    assert resp.request.method == "PUT"
    assert "?database=Documents" in resp.request.url
    assert "Content-Type" in resp.request.headers
    assert resp.request.headers["Content-Type"] == "application/xml"
    assert resp.request.body == "<document/>"
    assert resp.status_code == 201


@responses.activate
def test_put_with_customized_params_and_headers_and_json_body():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_content_type("application/json")
    builder.with_request_param("database", "Documents")
    builder.with_request_param("uri", "/doc.json")
    builder.with_request_body({"document": {}})
    builder.with_response_status(201)
    builder.with_empty_response_body()
    builder.build_put()

    with MLClient(auth_method="digest") as client:
        resp = client.put(
            "/v1/documents",
            body={"document": {}},
            params={"database": "Documents", "uri": "/doc.json"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.request.method == "PUT"
    assert "?database=Documents" in resp.request.url
    assert "Content-Type" in resp.request.headers
    assert resp.request.headers["Content-Type"] == "application/json"
    assert resp.request.body == b'{"document": {}}'
    assert resp.status_code == 201


@responses.activate
def test_delete():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases/custom-db")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    with MLClient(auth_method="digest") as client:
        resp = client.delete_("/manage/v2/databases/custom-db")

    assert resp.request.method == "DELETE"
    assert "?" not in resp.request.url
    assert resp.status_code == 204
    assert not resp.text


@responses.activate
def test_delete_with_customized_params_and_headers():
    builder = MLResponseBuilder()
    builder.with_method("DELETE")
    builder.with_base_url("http://localhost:8002/manage/v2/databases/custom-db")
    builder.with_request_param("format", "json")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build()

    with MLClient(auth_method="digest") as client:
        resp = client.delete_(
            "/manage/v2/databases/custom-db",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )

    assert resp.request.method == "DELETE"
    assert "?format=json" in resp.request.url
    assert "custom-header" in resp.request.headers
    assert resp.request.headers["custom-header"] == "custom-value"
    assert resp.status_code == 204
    assert not resp.text
