"""DocumentsApi - mid-level access to MarkLogic documents endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import DocumentsDeleteCall, DocumentsGetCall, DocumentsPostCall
from mlclient.structures.calls import DocumentsBodyPart

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class DocumentsApi:
    """Mid-level API for /v1/documents endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get(
        self,
        uri: str | list,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        timestamp: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
    ) -> Response:
        """Send a GET request to the /v1/documents endpoint."""
        call = DocumentsGetCall(
            uri=uri,
            database=database,
            category=category,
            data_format=data_format,
            timestamp=timestamp,
            transform=transform,
            transform_params=transform_params,
            txid=txid,
        )
        return self._rest.call(call)

    def post(
        self,
        body_parts: list[DocumentsBodyPart],
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
    ) -> Response:
        """Send a POST request to the /v1/documents endpoint."""
        call = DocumentsPostCall(
            body_parts=body_parts,
            database=database,
            transform=transform,
            transform_params=transform_params,
            txid=txid,
            temporal_collection=temporal_collection,
            system_time=system_time,
        )
        return self._rest.call(call)

    def delete(
        self,
        uri: str | list,
        database: str | None = None,
        category: str | list | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        wipe_temporal: bool | None = None,
    ) -> Response:
        """Send a DELETE request to the /v1/documents endpoint."""
        call = DocumentsDeleteCall(
            uri=uri,
            database=database,
            category=category,
            txid=txid,
            temporal_collection=temporal_collection,
            system_time=system_time,
            wipe_temporal=wipe_temporal,
        )
        return self._rest.call(call)
