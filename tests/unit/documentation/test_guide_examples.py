import httpx
import pytest
import respx

from docs.examples.collections import replace_collection
from docs.examples.custom_api import AppClient, AsyncAppClient
from mlclient import MLClient


@respx.mock
def test_custom_client_uses_shared_transport_and_request_timeout():
    route = respx.get("http://localhost:8100/app/tasks", params={"status": "open"})
    route.mock(return_value=httpx.Response(200, json={"tasks": [{"title": "Review"}]}))
    with AppClient(port=8100, auth=None) as ml:
        assert ml.open_task_titles(timeout=2) == ["Review"]
    assert route.calls.last.request.extensions["timeout"]["read"] == 2
    assert not ml.is_connected()


@pytest.mark.asyncio
@respx.mock
async def test_async_custom_client_uses_shared_transport_and_request_timeout():
    route = respx.get("http://localhost:8100/app/tasks", params={"status": "open"})
    route.mock(return_value=httpx.Response(200, json={"tasks": [{"title": "Review"}]}))
    async with AsyncAppClient(port=8100, auth=None) as ml:
        assert await ml.open_task_titles(timeout=2) == ["Review"]
    assert route.calls.last.request.extensions["timeout"]["read"] == 2
    assert not ml.is_connected()


@respx.mock
def test_custom_client_does_not_hide_http_errors():
    respx.get("http://localhost:8100/app/tasks").mock(return_value=httpx.Response(403))
    with AppClient(port=8100, auth=None) as ml, pytest.raises(httpx.HTTPStatusError):
        ml.open_task_titles()


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
