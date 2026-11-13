"""Higher-level Documents service (DocumentsService / AsyncDocumentsService).

Provides parsed document operations on MarkLogic.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

from mlclient import _constants as constants
from mlclient._options import UNSET
from mlclient.exceptions import WrongParametersError

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi

from mlclient.models.document_parts import Category, DocumentsBodyPart
from mlclient.models.documents import Document, Metadata, MetadataDocument
from mlclient.models.mimetypes import Mimetypes
from mlclient.responses import MLResponseParser
from mlclient.services._documents_parsing import DocumentsReader, normalize_category
from mlclient.services.scope import ServiceScope

_MAX_QUERY_BYTES = 48 * 1024
"""Soft limit on the total size of ``uri=...`` query parameters per request.

httpx enforces MAX_URL_LENGTH = 65536 bytes on the whole URL. Setting the
per-batch budget at 48 KiB (75% of that limit) leaves headroom for the base
URL, the endpoint path, and other query parameters (``database``, ``category``,
``format``).
"""

_URI_PARAM_OVERHEAD = len("&uri=")


def _batched_uris(
    uris: str | list[str] | tuple[str] | set[str],
    max_query_bytes: int = _MAX_QUERY_BYTES,
) -> Iterator[str | list[str]]:
    """Split URIs into batches whose combined query length stays under a limit.

    Each URI contributes ``&uri=<uri>`` to the query string. A batch is closed
    as soon as adding the next URI would push the running byte total past
    ``max_query_bytes``. Single-string input is yielded as-is so
    DocumentsGetCall keeps its non-multipart accept header path. A URI longer
    than the budget on its own is still yielded alone - httpx will raise an
    explicit error rather than silently truncating.
    """
    if isinstance(uris, str):
        yield uris
        return
    batch: list[str] = []
    batch_bytes = 0
    for uri in uris:
        uri_bytes = _URI_PARAM_OVERHEAD + len(uri.encode("utf-8"))
        if batch and batch_bytes + uri_bytes > max_query_bytes:
            yield batch
            batch = []
            batch_bytes = 0
        batch.append(uri)
        batch_bytes += uri_bytes
    if batch:
        yield batch


class DocumentsService:
    """Higher-level service for /v1/documents CRUD operations.

    Notes
    -----
    MarkLogic's REST API (App-Services, port 8000) and Manage API (port 8002)
    return different HTTP status codes for the same underlying errors. For
    example, RESTAPI-NODOCUMENT and XDMP-DOCNOTFOUND are returned as
    **404 Not Found** on the REST API but as **500 Internal Server Error**
    on the Manage API. This is due to different error handler mappings on
    each port.
    """

    def __init__(self, rest: RestApi, scope: ServiceScope | None = None):
        """Create a service on the supplied REST connection.

        Parameters
        ----------
        rest : RestApi
            REST transport shared by this service and its scoped copies.
        scope : ServiceScope | None, default None
            Database and transaction defaults; None uses an empty scope.
        """
        self._rest = rest
        self._scope = ServiceScope().overridden_by(scope)

    def __call__(
        self,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
    ) -> DocumentsService:
        """Return a scoped copy without opening a connection or a transaction.

        Parameters
        ----------
        database : str | None, default unset
            Content database; unset inherits, None clears the inherited value.
        txid : str | None, default unset
            Transaction identifier; unset inherits, None clears the inherited value.

        Returns
        -------
        DocumentsService
            A new service using the same REST transport and the merged scope.
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        return DocumentsService(self._rest, scope)

    def write(
        self,
        data: Document | Metadata | list[Document | Metadata],
        *,
        transform: str | None = None,
        transform_params: dict | None = None,
        database: str | None = UNSET,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> dict:
        """Write (create or update) document(s) content or metadata.

        Parameters
        ----------
        data : Document | Metadata | list[Document | Metadata]
            One or more document or default metadata.
        transform : str | None, default None
            Name of a transform installed through ``/v1/config/transforms``.
            MarkLogic applies it to content parts only and stores its output.
        transform_params : dict | None, default None
            Transform parameters, sent as ``trans:{name}``; requires transform.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        temporal_collection : str | None, default None
            Temporal collection name.
        system_time : str | None, default None
            System start time (an ISO 8601 dateTime) overriding the one set by
            MarkLogic; requires temporal_collection and the
            ``temporal-statement-set-system-time`` privilege.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Returns
        -------
        dict
            An origin response from a MarkLogic server.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        WrongParametersError
            If system_time is given without temporal_collection, or
            transform_params without transform.
        """
        _validate_write_params(
            transform=transform,
            transform_params=transform_params,
            temporal_collection=temporal_collection,
            system_time=system_time,
        )
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        params = scope.request_params()
        body_parts = _DocumentsSender.parse(data)
        resp = self._rest.documents.post(
            body_parts,
            database=params["database"],
            transform=transform,
            transform_params=transform_params,
            txid=params["txid"],
            temporal_collection=temporal_collection,
            system_time=system_time,
            timeout=timeout,
        )
        MLResponseParser.raise_for_status(resp)
        return MLResponseParser.parse(resp)

    def read(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> Document | dict[str, Document]:
        """Return document(s) content or metadata from a MarkLogic database.

        When uris is a string it returns a single Document instance. Otherwise,
        result is a dict mapping URI to Document.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : Category | str | list[Category | str] | None, default None
            The category of data to fetch about the requested document.
        transform : str | None, default None
            Name of a transform installed through ``/v1/config/transforms``.
            MarkLogic applies it to content only; metadata is returned
            untransformed.
        transform_params : dict | None, default None
            Transform parameters, sent as ``trans:{name}``; requires transform.
        timestamp : str | None, default None
            Point in time to read at - the ``ML-Effective-Timestamp`` of an
            earlier response, such as ``SearchReport.effective_timestamp``.
            Every request of the operation uses it, so all documents come from
            one snapshot. The server must still retain that version
            (``XDMP-OLDSTAMP`` otherwise). Cannot be combined with a txid.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Returns
        -------
        Document | dict[str, Document]
            A single document when uris is a string, otherwise a dict keyed by URI.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        WrongParametersError
            If timestamp is combined with a txid (passed or inherited from the
            service scope), or transform_params are given without transform.
        """
        docs = self.read_stream(
            uris,
            category=category,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        return next(docs) if isinstance(uris, str) else {doc.uri: doc for doc in docs}

    def read_stream(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> Iterator[Document]:
        """Return document(s) as an iterator, suitable for batch processing.

        Unlike read(), does not materialize results into a dict. URIs are
        transparently split into batches whose combined query string stays below
        the httpx URL length limit; each batch is a separate HTTP request.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : Category | str | list[Category | str] | None, default None
            The category of data to fetch about the requested document.
        transform : str | None, default None
            Name of a transform installed through ``/v1/config/transforms``.
            MarkLogic applies it to content only; metadata is returned
            untransformed.
        transform_params : dict | None, default None
            Transform parameters, sent as ``trans:{name}``; requires transform.
        timestamp : str | None, default None
            Point in time to read at - the ``ML-Effective-Timestamp`` of an
            earlier response, such as ``SearchReport.effective_timestamp``.
            Every request of the operation uses it, so all documents come from
            one snapshot. The server must still retain that version
            (``XDMP-OLDSTAMP`` otherwise). Cannot be combined with a txid.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Returns
        -------
        Iterator[Document]
            Documents from the database.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        WrongParametersError
            If timestamp is combined with a txid (passed or inherited from the
            service scope), or transform_params are given without transform.
            Raised when iteration starts, before any request.
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        params = scope.request_params()
        _validate_read_params(
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            txid=params["txid"],
        )
        category = normalize_category(category)
        for batch in _batched_uris(uris):
            resp = self._rest.documents.get(
                batch,
                category=category,
                database=params["database"],
                data_format="json",
                timestamp=timestamp,
                transform=transform,
                transform_params=transform_params,
                txid=params["txid"],
                timeout=timeout,
            )
            MLResponseParser.raise_for_status(resp)
            yield from DocumentsReader.parse(resp, category, uris=batch)

    def delete(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = UNSET,
        temporal_collection: str | None = None,
        wipe_temporal: bool | None = None,
        txid: str | None = UNSET,
        timeout=UNSET,
    ):
        """Delete document(s) content or metadata in a MarkLogic database.

        URIs are transparently split into batches whose combined query string
        stays below the httpx URL length limit; each batch is a separate
        HTTP request.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            The URI of a document to delete.
        category : Category | str | list[Category | str] | None, default None
            The category of data to remove/reset.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        temporal_collection : str | None, default None
            Temporal collection name.
        wipe_temporal : bool | None, default None
            Remove all versions of a temporal document.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        params = scope.request_params()
        category = normalize_category(category)
        for batch in _batched_uris(uris):
            resp = self._rest.documents.delete(
                batch,
                category=category,
                database=params["database"],
                temporal_collection=temporal_collection,
                wipe_temporal=wipe_temporal,
                txid=params["txid"],
                timeout=timeout,
            )
            MLResponseParser.raise_for_status(resp)


class _DocumentsSender:
    """A class parsing Document or Metadata instance(s) to DocumentsBodyPart's list."""

    @classmethod
    def parse(
        cls,
        data: Document | Metadata | list[Document | Metadata],
    ) -> list[DocumentsBodyPart]:
        """Parse Document or Metadata instance(s) to DocumentsBodyPart's list."""
        if not isinstance(data, list):
            data = [data]
        body_parts = []
        for data_unit in data:
            if type(data_unit) not in (Metadata, MetadataDocument):
                if data_unit.metadata is not None:
                    new_parts = [
                        cls._get_doc_metadata_body_part(data_unit),
                        cls._get_doc_content_body_part(data_unit),
                    ]
                else:
                    new_parts = [cls._get_doc_content_body_part(data_unit)]
            elif type(data_unit) is not Metadata:
                new_parts = [cls._get_doc_metadata_body_part(data_unit)]
            else:
                new_parts = [cls._get_default_metadata_body_part(data_unit)]
            body_parts.extend(new_parts)
        return body_parts

    @classmethod
    def _get_doc_content_body_part(
        cls,
        document: Document,
    ) -> DocumentsBodyPart:
        """Instantiate DocumentsBodyPart with Document's content."""
        return DocumentsBodyPart(
            **{
                "content-type": Mimetypes.get_mimetype(document.uri),
                "content-disposition": {
                    "type": "attachment",
                    "filename": document.uri,
                    "format": document.doc_type,
                },
                "content": document.content_bytes,
            },
        )

    @classmethod
    def _get_doc_metadata_body_part(
        cls,
        document: Document,
    ) -> DocumentsBodyPart:
        """Instantiate DocumentsBodyPart with Document's metadata."""
        return DocumentsBodyPart(
            **{
                "content-type": constants.HEADER_JSON,
                "content-disposition": {
                    "type": "attachment",
                    "filename": document.uri,
                    "category": "metadata",
                },
                "content": document.metadata.to_json_string(),
            },
        )

    @classmethod
    def _get_default_metadata_body_part(
        cls,
        metadata: Metadata,
    ) -> DocumentsBodyPart:
        """Instantiate DocumentsBodyPart with default metadata."""
        return DocumentsBodyPart(
            **{
                "content-type": constants.HEADER_JSON,
                "content-disposition": {
                    "type": "inline",
                    "category": "metadata",
                },
                "content": metadata.to_json_string(),
            },
        )


class AsyncDocumentsService:
    """Async higher-level service for /v1/documents CRUD operations."""

    def __init__(self, rest: AsyncRestApi, scope: ServiceScope | None = None):
        """Create a service on the supplied REST connection.

        Parameters
        ----------
        rest : AsyncRestApi
            REST transport shared by this service and its scoped copies.
        scope : ServiceScope | None, default None
            Database and transaction defaults; None uses an empty scope.
        """
        self._rest = rest
        self._scope = ServiceScope().overridden_by(scope)

    def __call__(
        self,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
    ) -> AsyncDocumentsService:
        """Return a scoped copy without opening a connection or a transaction.

        Parameters
        ----------
        database : str | None, default unset
            Content database; unset inherits, None clears the inherited value.
        txid : str | None, default unset
            Transaction identifier; unset inherits, None clears the inherited value.

        Returns
        -------
        AsyncDocumentsService
            A new service using the same REST transport and the merged scope.
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        return AsyncDocumentsService(self._rest, scope)

    async def write(
        self,
        data: Document | Metadata | list[Document | Metadata],
        *,
        transform: str | None = None,
        transform_params: dict | None = None,
        database: str | None = UNSET,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> dict:
        """Write (create or update) document(s) content or metadata.

        Parameters
        ----------
        data : Document | Metadata | list[Document | Metadata]
            One or more document or default metadata.
        transform : str | None, default None
            Name of a transform installed through ``/v1/config/transforms``.
            MarkLogic applies it to content parts only and stores its output.
        transform_params : dict | None, default None
            Transform parameters, sent as ``trans:{name}``; requires transform.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        temporal_collection : str | None, default None
            Temporal collection name.
        system_time : str | None, default None
            System start time (an ISO 8601 dateTime) overriding the one set by
            MarkLogic; requires temporal_collection and the
            ``temporal-statement-set-system-time`` privilege.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Returns
        -------
        dict
            An origin response from a MarkLogic server.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        WrongParametersError
            If system_time is given without temporal_collection, or
            transform_params without transform.
        """
        _validate_write_params(
            transform=transform,
            transform_params=transform_params,
            temporal_collection=temporal_collection,
            system_time=system_time,
        )
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        params = scope.request_params()
        body_parts = _DocumentsSender.parse(data)
        resp = await self._rest.documents.post(
            body_parts,
            database=params["database"],
            transform=transform,
            transform_params=transform_params,
            txid=params["txid"],
            temporal_collection=temporal_collection,
            system_time=system_time,
            timeout=timeout,
        )
        MLResponseParser.raise_for_status(resp)
        return MLResponseParser.parse(resp)

    async def read(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> Document | dict[str, Document]:
        """Return document(s) content or metadata from a MarkLogic database.

        When uris is a string it returns a single Document instance. Otherwise,
        result is a dict mapping URI to Document.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : Category | str | list[Category | str] | None, default None
            The category of data to fetch about the requested document.
        transform : str | None, default None
            Name of a transform installed through ``/v1/config/transforms``.
            MarkLogic applies it to content only; metadata is returned
            untransformed.
        transform_params : dict | None, default None
            Transform parameters, sent as ``trans:{name}``; requires transform.
        timestamp : str | None, default None
            Point in time to read at - the ``ML-Effective-Timestamp`` of an
            earlier response, such as ``SearchReport.effective_timestamp``.
            Every request of the operation uses it, so all documents come from
            one snapshot. The server must still retain that version
            (``XDMP-OLDSTAMP`` otherwise). Cannot be combined with a txid.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Returns
        -------
        Document | dict[str, Document]
            A single document when uris is a string, otherwise a dict keyed by URI.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        WrongParametersError
            If timestamp is combined with a txid (passed or inherited from the
            service scope), or transform_params are given without transform.
        """
        stream = self.read_stream(
            uris,
            category=category,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        if isinstance(uris, str):
            return await stream.__anext__()
        return {doc.uri: doc async for doc in stream}

    async def read_stream(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> AsyncIterator[Document]:
        """Return document(s) as an iterator, suitable for batch processing.

        Unlike read(), does not materialize results into a dict. URIs are
        transparently split into batches whose combined query string stays below
        the httpx URL length limit; each batch is a separate HTTP request.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : Category | str | list[Category | str] | None, default None
            The category of data to fetch about the requested document.
        transform : str | None, default None
            Name of a transform installed through ``/v1/config/transforms``.
            MarkLogic applies it to content only; metadata is returned
            untransformed.
        transform_params : dict | None, default None
            Transform parameters, sent as ``trans:{name}``; requires transform.
        timestamp : str | None, default None
            Point in time to read at - the ``ML-Effective-Timestamp`` of an
            earlier response, such as ``SearchReport.effective_timestamp``.
            Every request of the operation uses it, so all documents come from
            one snapshot. The server must still retain that version
            (``XDMP-OLDSTAMP`` otherwise). Cannot be combined with a txid.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Returns
        -------
        AsyncIterator[Document]
            Documents from the database.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        WrongParametersError
            If timestamp is combined with a txid (passed or inherited from the
            service scope), or transform_params are given without transform.
            Raised when iteration starts, before any request.
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        params = scope.request_params()
        _validate_read_params(
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            txid=params["txid"],
        )
        category = normalize_category(category)
        for batch in _batched_uris(uris):
            resp = await self._rest.documents.get(
                batch,
                category=category,
                database=params["database"],
                data_format="json",
                timestamp=timestamp,
                transform=transform,
                transform_params=transform_params,
                txid=params["txid"],
                timeout=timeout,
            )
            MLResponseParser.raise_for_status(resp)
            for doc in DocumentsReader.parse(resp, category, uris=batch):
                yield doc

    async def delete(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = UNSET,
        temporal_collection: str | None = None,
        wipe_temporal: bool | None = None,
        txid: str | None = UNSET,
        timeout=UNSET,
    ):
        """Delete document(s) content or metadata in a MarkLogic database.

        URIs are transparently split into batches whose combined query string
        stays below the httpx URL length limit; each batch is a separate
        HTTP request.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            The URI of a document to delete.
        category : Category | str | list[Category | str] | None, default None
            The category of data to remove/reset.
        database : str | None, default unset
            Content database; unset inherits the service scope and None clears it.
        temporal_collection : str | None, default None
            Temporal collection name.
        wipe_temporal : bool | None, default None
            Remove all versions of a temporal document.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.
            When the operation issues several requests it applies to each of
            them independently, not as a shared budget, and is not persisted.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        """
        scope = self._scope.overridden_by(ServiceScope(database=database, txid=txid))
        params = scope.request_params()
        category = normalize_category(category)
        for batch in _batched_uris(uris):
            resp = await self._rest.documents.delete(
                batch,
                category=category,
                database=params["database"],
                temporal_collection=temporal_collection,
                wipe_temporal=wipe_temporal,
                txid=params["txid"],
                timeout=timeout,
            )
            MLResponseParser.raise_for_status(resp)


def _validate_read_params(
    *,
    transform: str | None,
    transform_params: dict | None,
    timestamp: str | None,
    txid: str | None,
):
    """Reject read parameters that MarkLogic cannot combine.

    A point-in-time read inside a transaction fails on the server with a 500
    ``XDMP-UPDATETIMESTAMP`` error, so it is rejected before any request.

    Raises
    ------
    WrongParametersError
        If timestamp is combined with txid, or transform_params are given
        without transform.
    """
    if timestamp is not None and txid is not None:
        msg = "timestamp cannot be combined with txid"
        raise WrongParametersError(msg)
    _validate_transform_params(transform, transform_params)


def _validate_write_params(
    *,
    transform: str | None,
    transform_params: dict | None,
    temporal_collection: str | None,
    system_time: str | None,
):
    """Reject write parameters that MarkLogic would ignore.

    Raises
    ------
    WrongParametersError
        If system_time is given without temporal_collection, or
        transform_params without transform.
    """
    if system_time is not None and temporal_collection is None:
        msg = "system_time requires temporal_collection"
        raise WrongParametersError(msg)
    _validate_transform_params(transform, transform_params)


def _validate_transform_params(transform: str | None, transform_params: dict | None):
    """Reject transform parameters sent without a transform to receive them.

    Raises
    ------
    WrongParametersError
        If transform_params are given without transform.
    """
    if transform_params and transform is None:
        msg = "transform_params require transform"
        raise WrongParametersError(msg)
