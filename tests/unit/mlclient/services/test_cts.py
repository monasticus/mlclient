from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.services import AsyncCtsService, CtsService


@pytest.mark.parametrize("selection", [{}, {"index": 2}, {"range": [2, 3]}])
@respx.mock
def test_search_projects_after_selection_with_shared_namespaces(selection):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, content=b""),
    )
    with MLClient() as ml:
        assert (
            CtsService(ml.rest, namespaces={"p": "urn:old"}).search(
                xpath="p:item/p:title",
                namespaces={"p": "urn:new"},
                **selection,
            )
            == []
        )
    body = parse_qs(route.calls.last.request.content.decode())
    source = body["xquery"][0]
    bindings = json.loads(body["vars"][0])
    assert 'declare namespace p = "urn:new";' in source
    assert 'kind="projection"' in source
    assert "cts:valid-extract-path(" in source
    assert "p:item/p:title" in bindings.values()
    assert "p:item/p:title" not in source
    template = next(value for value in bindings.values() if " ! (" in value)
    assert "cts:search((/), ())" in template
    if selection:
        assert template.index("]") < template.index(" ! (")


@pytest.mark.asyncio
@pytest.mark.parametrize("selection", [{}, {"index": 2}, {"range": [2, 3]}])
@respx.mock
async def test_async_search_projects_after_selection_with_shared_namespaces(selection):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, content=b""),
    )
    async with AsyncMLClient() as ml:
        assert (
            await AsyncCtsService(ml.rest, namespaces={"p": "urn:old"}).search(
                xpath="p:item/p:title",
                namespaces={"p": "urn:new"},
                **selection,
            )
            == []
        )
    body = parse_qs(route.calls.last.request.content.decode())
    source = body["xquery"][0]
    bindings = json.loads(body["vars"][0])
    assert 'declare namespace p = "urn:new";' in source
    assert 'kind="projection"' in source
    assert "cts:valid-extract-path(" in source
    assert "p:item/p:title" in bindings.values()
    assert "p:item/p:title" not in source
    template = next(value for value in bindings.values() if " ! (" in value)
    assert "cts:search((/), ())" in template
    if selection:
        assert template.index("]") < template.index(" ! (")


@pytest.mark.parametrize(
    ("path", "error"),
    [("", ValueError), ("  ", ValueError), (1, TypeError)],
)
@respx.mock
def test_search_rejects_invalid_projection_before_io(path, error):
    with MLClient() as ml, pytest.raises(error, match="xpath"):
        CtsService(ml.rest).search(xpath=path)
    assert not respx.calls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "error"),
    [("", ValueError), ("  ", ValueError), (1, TypeError)],
)
@respx.mock
async def test_async_search_rejects_invalid_projection_before_io(path, error):
    async with AsyncMLClient() as ml:
        with pytest.raises(error, match="xpath"):
            await AsyncCtsService(ml.rest).search(xpath=path)
    assert not respx.calls


@respx.mock
def test_lexicon_queries_require_explicit_keywords():
    with MLClient() as ml:
        service = CtsService(ml.rest)
        with pytest.raises(TypeError):
            service.uris(service.true_query())
        with pytest.raises(TypeError):
            service.values(service.uri_reference(), service.true_query())
    assert not respx.calls


@pytest.mark.asyncio
@respx.mock
async def test_async_lexicon_queries_require_explicit_keywords():
    async with AsyncMLClient() as ml:
        service = AsyncCtsService(ml.rest)
        with pytest.raises(TypeError):
            await service.uris(service.true_query())
        with pytest.raises(TypeError):
            await service.values(service.uri_reference(), service.true_query())
    assert not respx.calls
