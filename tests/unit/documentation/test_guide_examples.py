from pathlib import Path

import httpx
import pytest
import respx

from docs.examples.cluster_hosts import eval_on_each_host
from docs.examples.collections import replace_collection
from docs.examples.custom_api import AppClient, AsyncAppClient
from docs.examples.database_counts import count_documents
from mlclient import MLClient, MLClientManager
from tests.utils.ml_mockers import MLRespXMocker


@respx.mock
def test_custom_client_service_parses_and_forwards_request_timeout():
    route = respx.get("http://localhost:8100/app/tasks", params={"status": "open"})
    route.mock(return_value=httpx.Response(200, json={"tasks": [{"title": "Review"}]}))
    with AppClient(port=8100, auth=None) as ml:
        assert ml.tasks.open_titles(timeout=2) == ["Review"]
    assert route.calls.last.request.extensions["timeout"]["read"] == 2
    assert not ml.is_connected()


@respx.mock
def test_custom_client_api_returns_raw_response():
    route = respx.get("http://localhost:8100/app/tasks", params={"status": "open"})
    route.mock(return_value=httpx.Response(200, json={"tasks": [{"title": "Review"}]}))
    with AppClient(port=8100, auth=None) as ml:
        response = ml.rest.tasks.list()
        assert response.status_code == 200
        assert response.json() == {"tasks": [{"title": "Review"}]}


@pytest.mark.asyncio
@respx.mock
async def test_async_custom_client_service_parses_and_forwards_request_timeout():
    route = respx.get("http://localhost:8100/app/tasks", params={"status": "open"})
    route.mock(return_value=httpx.Response(200, json={"tasks": [{"title": "Review"}]}))
    async with AsyncAppClient(port=8100, auth=None) as ml:
        assert await ml.tasks.open_titles(timeout=2) == ["Review"]
    assert route.calls.last.request.extensions["timeout"]["read"] == 2
    assert not ml.is_connected()


@respx.mock
def test_custom_client_does_not_hide_http_errors():
    respx.get("http://localhost:8100/app/tasks").mock(return_value=httpx.Response(403))
    with AppClient(port=8100, auth=None) as ml, pytest.raises(httpx.HTTPStatusError):
        ml.tasks.open_titles()


@respx.mock
def test_collection_recipe_preserves_metadata_and_sends_no_content():
    respx.post("http://localhost:8000/v1/transactions").mock(
        return_value=httpx.Response(303, headers={"Location": "/v1/transactions/123"}),
    )
    respx.get(
        "http://localhost:8000/v1/documents",
        params={"uri": "/x.json", "category": "metadata", "txid": "123"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "collections": ["pending", "invoices"],
                "quality": 7,
                "permissions": [{"role-name": "reader", "capabilities": ["read"]}],
                "properties": {},
                "metadataValues": {"source": "import"},
            },
        ),
    )
    write = respx.post("http://localhost:8000/v1/documents", params={"txid": "123"})
    write.mock(return_value=httpx.Response(200, json={}))
    commit = respx.post(
        "http://localhost:8000/v1/transactions/123",
        params={"result": "commit"},
    ).mock(return_value=httpx.Response(204))
    with MLClient(auth=None) as ml:
        assert replace_collection(ml, "/x.json", "pending", "processed")
    body = write.calls.last.request.content
    for marker in (b"processed", b"invoices", b"reader", b"import", b'"quality": 7'):
        assert marker in body
    assert b"pending" not in body
    assert b"category=metadata" in body
    assert b"category=content" not in body
    assert commit.called


@pytest.mark.parametrize("name", ["", "   "])
def test_collection_recipe_rejects_blank_destination_before_io(name):
    with (
        MLClient(auth=None) as ml,
        pytest.raises(ValueError, match="must not be blank"),
    ):
        replace_collection(ml, "/x.json", "pending", name)


@pytest.mark.asyncio
@respx.mock
async def test_database_counts_recipe_routes_each_eval_to_its_database():
    ml_mocker = MLRespXMocker(use_router=False)
    for database, count in (("Documents", 12), ("Modules", 3)):
        ml_mocker.with_url("http://localhost:8000/v1/eval")
        ml_mocker.with_request_param("database", database)
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"xquery": "fn:count(fn:collection())"})
        ml_mocker.with_response_code(200)
        ml_mocker.with_response_body_part("integer", str(count))
        ml_mocker.mock_post()

    assert await count_documents(["Documents", "Modules"]) == {
        "Documents": 12,
        "Modules": 3,
    }


@pytest.mark.asyncio
@respx.mock
async def test_cluster_hosts_recipe_routes_query_to_each_host():
    ml_mocker = MLRespXMocker(use_router=False)
    for host in ("node-1.example", "node-2.example"):
        ml_mocker.with_url(f"http://{host}:8000/v1/eval")
        ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
        ml_mocker.with_request_body({"xquery": "xdmp:host-name()"})
        ml_mocker.with_response_code(200)
        ml_mocker.with_response_body_part("string", host)
        ml_mocker.mock_post()

    assert await eval_on_each_host(
        ["node-1.example", "node-2.example"],
        "xdmp:host-name()",
    ) == {
        "node-1.example": "node-1.example",
        "node-2.example": "node-2.example",
    }


@respx.mock
def test_basic_environment_example_works_from_a_project_subdirectory(
    tmp_path,
    monkeypatch,
):
    yaml = Path("docs/user/environments/mlclient-local.yaml").read_text()
    config_dir = tmp_path / ".mlclient"
    config_dir.mkdir()
    (config_dir / "mlclient-local.yaml").write_text(yaml)
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    monkeypatch.chdir(source_dir)

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8100/v1/eval")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": '"Hello World!"'})
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "Hello World!")
    ml_mocker.mock_post()

    manager = MLClientManager("local")
    with manager.get_client() as ml:
        assert ml.eval.xquery('"Hello World!"') == "Hello World!"
    assert manager.config.app_server_ids == [
        "content",
        "app-services",
        "manage",
        "admin",
        "health",
    ]
