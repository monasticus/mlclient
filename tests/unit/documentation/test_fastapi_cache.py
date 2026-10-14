"""Optional FastAPI recipe checks; install FastAPI to run these tests."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

pytest.importorskip("fastapi")
spec = importlib.util.spec_from_file_location(
    "fastapi_cache",
    Path(__file__).parents[3] / "docs/examples/fastapi_cache.py",
)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


def client_with_cache(cached):
    response = httpx.Response(
        404 if cached is None else 200,
        json=cached,
        request=httpx.Request("GET", "http://marklogic/v1/documents"),
    )
    return SimpleNamespace(
        rest=SimpleNamespace(
            documents=SimpleNamespace(get=AsyncMock(return_value=response)),
        ),
        documents=SimpleNamespace(write=AsyncMock()),
    )


def upstream_response(status, data=None, etag=None):
    return httpx.Response(
        status,
        json=data,
        headers={"ETag": etag} if etag else {},
        request=httpx.Request("GET", recipe.SOURCE_URL),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("cached", [None, {"etag": '"old"', "data": {"stars": 1}}])
async def test_new_or_changed_source_updates_the_document(cached):
    ml = client_with_cache(cached)
    http = SimpleNamespace(
        get=AsyncMock(return_value=upstream_response(200, {"stars": 2}, '"new"')),
    )
    result = await recipe.cached_repository(ml, http)
    assert result == {"cache": "updated", "data": {"stars": 2}}
    document = ml.documents.write.call_args.args[0]
    assert document.uri == recipe.CACHE_URI
    assert document.content == {"etag": '"new"', "data": {"stars": 2}}
    expected = {"If-None-Match": '"old"'} if cached else {}
    http.get.assert_awaited_once_with(recipe.SOURCE_URL, headers=expected)


@pytest.mark.asyncio
async def test_unchanged_source_does_not_rewrite_cache():
    cached = {"etag": '"same"', "data": {"stars": 1}}
    ml = client_with_cache(cached)
    http = SimpleNamespace(get=AsyncMock(return_value=upstream_response(304)))
    assert await recipe.cached_repository(ml, http) == {
        "cache": "validated",
        "data": cached["data"],
    }
    ml.documents.write.assert_not_awaited()
    http.get.assert_awaited_once_with(
        recipe.SOURCE_URL, headers={"If-None-Match": '"same"'},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("transport_failure", [False, True])
@pytest.mark.parametrize("cached", [None, {"etag": None, "data": {"stars": 1}}])
async def test_source_failure_uses_saved_data_only_when_available(
    transport_failure, cached,
):
    ml = client_with_cache(cached)
    get = (
        AsyncMock(side_effect=httpx.ConnectError("offline"))
        if transport_failure
        else AsyncMock(return_value=upstream_response(503))
    )
    http = SimpleNamespace(get=get)
    if cached:
        assert await recipe.cached_repository(ml, http) == {
            "cache": "stale",
            "data": cached["data"],
        }
    else:
        with pytest.raises(recipe.HTTPException) as raised:
            await recipe.cached_repository(ml, http)
        assert raised.value.status_code == 503
    ml.documents.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_source_client_error_is_not_masked_by_stale_cache():
    ml = client_with_cache({"etag": '"old"', "data": {"stars": 1}})
    http = SimpleNamespace(get=AsyncMock(return_value=upstream_response(404)))
    with pytest.raises(recipe.HTTPException) as raised:
        await recipe.cached_repository(ml, http)
    assert raised.value.status_code == 502
    ml.documents.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_etag_uses_an_unconditional_request():
    ml = client_with_cache({"etag": None, "data": {"stars": 1}})
    http = SimpleNamespace(
        get=AsyncMock(return_value=upstream_response(200, {"stars": 2})),
    )
    await recipe.cached_repository(ml, http)
    http.get.assert_awaited_once_with(recipe.SOURCE_URL, headers={})
