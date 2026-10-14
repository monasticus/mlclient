"""Cache a public GitHub repository response in MarkLogic with ETag validation."""

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request

from mlclient import AsyncMLClient
from mlclient.models import Document

SOURCE_URL = "https://api.github.com/repos/monasticus/mlclient"
CACHE_URI = "/cache/github/mlclient.json"


async def cached_repository(ml, http):
    """Revalidate the saved response; serve stale data only on upstream failure."""
    response = await ml.rest.documents.get(CACHE_URI)
    if response.status_code == 404:
        cached = None
    else:
        response.raise_for_status()
        cached = response.json()
    headers = {"If-None-Match": cached["etag"]} if cached and cached["etag"] else {}
    try:
        response = await http.get(SOURCE_URL, headers=headers)
        if response.status_code == 304 and cached:
            return {"cache": "validated", "data": cached["data"]}
        response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as error:
        if (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code < 500
        ):
            raise HTTPException(502, "Source rejected the request") from error
        if cached:
            return {"cache": "stale", "data": cached["data"]}
        raise HTTPException(503, "Source unavailable and no cached response") from error
    data = response.json()
    await ml.documents.write(
        Document.create(
            CACHE_URI, {"etag": response.headers.get("etag"), "data": data}
        ),
    )
    return {"cache": "updated", "data": data}


@asynccontextmanager
async def lifespan(app):
    """Share both clients for the application lifetime and close them at shutdown."""
    async with AsyncMLClient() as ml, httpx.AsyncClient(timeout=5) as http:
        app.state.ml = ml
        app.state.http = http
        # shortcut: one worker; use shared refresh coordination for multiple workers.
        app.state.refresh = asyncio.Lock()
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/repository")
async def repository(request: Request):
    """Return repository metadata, validated against the source on every request."""
    async with request.app.state.refresh:
        return await cached_repository(request.app.state.ml, request.app.state.http)
