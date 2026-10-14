"""Serve a MarkLogic JSON document through a small async FastAPI cache."""

import asyncio
from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI, HTTPException, Request

from mlclient import AsyncMLClient

DOCUMENT_URI = "/products/coffee.json"
CACHE_SECONDS = 5


@asynccontextmanager
async def lifespan(app):
    """Keep one MarkLogic client open until application shutdown."""
    async with AsyncMLClient() as ml:
        app.state.ml = ml
        app.state.cache = None
        app.state.refresh = asyncio.Lock()
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/product")
async def product(request: Request):
    """Return cached JSON, fetching it from MarkLogic only on a cache miss."""
    state = request.app.state
    async with state.refresh:
        if state.cache and monotonic() < state.cache["expires_at"]:
            return {"cached": True, "product": state.cache["document"]}
        response = await state.ml.rest.documents.get(DOCUMENT_URI)
        if response.status_code == 404:
            raise HTTPException(404, "Product not found")
        response.raise_for_status()
        document = response.json()
        state.cache = {
            "expires_at": monotonic() + CACHE_SECONDS,
            "document": document,
        }
        return {"cached": False, "product": document}
