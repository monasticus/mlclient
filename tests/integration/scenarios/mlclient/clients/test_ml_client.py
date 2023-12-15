import pytest

from mlclient import MLClient


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


@pytest.mark.ml_access()
def test_get():
    with MLClient(auth_method="digest") as client:
        resp = client.get("/manage/v2/servers")

    assert resp.request.method == "GET"
    assert "?" not in resp.request.url
    assert resp.status_code == 200


@pytest.mark.ml_access()
def test_get_with_customized_params_and_headers():
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


@pytest.mark.ml_access()
def test_post():
    with MLClient(auth_method="digest") as client:
        resp = client.post("/manage/v2/databases/Documents")

    assert resp.request.method == "POST"
    assert "?" not in resp.request.url
    assert resp.request.body is None
    assert resp.status_code == 400


@pytest.mark.ml_access()
def test_post_with_customized_params_and_headers_and_body_different_than_json():
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


@pytest.mark.ml_access()
def test_post_with_customized_params_and_headers_and_json_body():
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


@pytest.mark.ml_access()
def test_put():
    with MLClient(auth_method="digest") as client:
        resp = client.put("/v1/documents")

    assert resp.request.method == "PUT"
    assert "?" not in resp.request.url
    assert resp.request.body is None
    assert resp.status_code == 400


@pytest.mark.ml_access()
def test_put_with_customized_params_and_headers_and_body_different_than_json():
    with MLClient(auth_method="digest") as client:
        resp = client.put(
            "/v1/documents",
            body="<document/>",
            params={"database": "Documents"},
            headers={"Content-Type": "application/xml"},
        )

    assert resp.request.method == "PUT"
    assert "?database=Documents" in resp.request.url
    assert "Content-Type" in resp.request.headers
    assert resp.request.headers["Content-Type"] == "application/xml"
    assert resp.request.body == "<document/>"
    assert resp.status_code == 400


@pytest.mark.ml_access()
def test_put_with_customized_params_and_headers_and_json_body():
    with MLClient(auth_method="digest") as client:
        resp = client.put(
            "/v1/documents",
            body={"document": {}},
            params={"database": "Documents"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.request.method == "PUT"
    assert "?database=Documents" in resp.request.url
    assert "Content-Type" in resp.request.headers
    assert resp.request.headers["Content-Type"] == "application/json"
    assert resp.request.body == b'{"document": {}}'
    assert resp.status_code == 400


@pytest.mark.ml_access()
def test_delete():
    with MLClient(auth_method="digest") as client:
        resp = client.delete_("/manage/v2/databases/custom-db")

    assert resp.request.method == "DELETE"
    assert "?" not in resp.request.url
    assert resp.status_code == 204
    assert not resp.text


@pytest.mark.ml_access()
def test_delete_with_customized_params_and_headers():
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
