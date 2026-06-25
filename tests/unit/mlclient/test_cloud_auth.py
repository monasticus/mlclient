from __future__ import annotations

import httpx
import pytest
import respx

from mlclient.auth import MarkLogicCloudAuth

BASE_URL = "https://example.marklogic.cloud"
TOKEN_URL = f"{BASE_URL}/token"
RESOURCE_URL = f"{BASE_URL}/ml/example/v1/documents"


def _cloud_auth(token_duration: int = 0) -> MarkLogicCloudAuth:
    return MarkLogicCloudAuth(
        base_url=BASE_URL,
        api_key="mk-123",
        token_duration=token_duration,
    )


@respx.mock
def test_token_fetched_on_first_request():
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok-1"}),
    )
    respx.get(RESOURCE_URL).mock(return_value=httpx.Response(200))

    with httpx.Client(auth=_cloud_auth()) as client:
        response = client.get(RESOURCE_URL)

    assert token_route.called
    assert response.request.headers["Authorization"] == "Bearer tok-1"


@respx.mock
def test_token_reused_across_requests():
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok-1"}),
    )
    respx.get(RESOURCE_URL).mock(return_value=httpx.Response(200))

    auth = _cloud_auth()
    with httpx.Client(auth=auth) as client:
        client.get(RESOURCE_URL)
        client.get(RESOURCE_URL)

    assert token_route.call_count == 1


@respx.mock
def test_token_refreshed_on_401():
    token_route = respx.post(TOKEN_URL).mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "tok-1"}),
            httpx.Response(200, json={"access_token": "tok-2"}),
        ],
    )
    respx.get(RESOURCE_URL).mock(
        side_effect=[httpx.Response(401), httpx.Response(200)],
    )

    auth = _cloud_auth()
    with httpx.Client(auth=auth) as client:
        response = client.get(RESOURCE_URL)

    assert token_route.call_count == 2
    assert response.status_code == 200
    assert response.request.headers["Authorization"] == "Bearer tok-2"


@respx.mock
def test_custom_duration_passed_to_token_endpoint():
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok-1"}),
    )
    respx.get(RESOURCE_URL).mock(return_value=httpx.Response(200))

    with httpx.Client(auth=_cloud_auth(token_duration=3600)) as client:
        client.get(RESOURCE_URL)

    assert token_route.calls.last.request.url.params["duration"] == "3600"


@respx.mock
def test_token_fetch_failure_raises():
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(500))
    respx.get(RESOURCE_URL).mock(return_value=httpx.Response(200))

    with (
        httpx.Client(auth=_cloud_auth()) as client,
        pytest.raises(
            httpx.HTTPStatusError,
        ),
    ):
        client.get(RESOURCE_URL)


@pytest.mark.asyncio
@respx.mock
async def test_async_token_fetched_on_first_request():
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok-1"}),
    )
    respx.get(RESOURCE_URL).mock(return_value=httpx.Response(200))

    async with httpx.AsyncClient(auth=_cloud_auth()) as client:
        response = await client.get(RESOURCE_URL)

    assert token_route.called
    assert response.request.headers["Authorization"] == "Bearer tok-1"


@pytest.mark.asyncio
@respx.mock
async def test_async_token_refreshed_on_401():
    token_route = respx.post(TOKEN_URL).mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "tok-1"}),
            httpx.Response(200, json={"access_token": "tok-2"}),
        ],
    )
    respx.get(RESOURCE_URL).mock(
        side_effect=[httpx.Response(401), httpx.Response(200)],
    )

    async with httpx.AsyncClient(auth=_cloud_auth()) as client:
        response = await client.get(RESOURCE_URL)

    assert token_route.call_count == 2
    assert response.request.headers["Authorization"] == "Bearer tok-2"
