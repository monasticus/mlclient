"""DocumentsApi / AsyncDocumentsApi - MarkLogic documents endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET, UnsetType
from mlclient.calls.documents import (
    DocumentsDeleteCall,
    DocumentsGetCall,
    DocumentsHeadCall,
    DocumentsPostCall,
)
from mlclient.models.document_parts import DocumentsBodyPart

if TYPE_CHECKING:
    import httpx

    from mlclient.clients.api import ApiClient, AsyncApiClient


class DocumentsApi:
    """Mid-level API for ``/v1/documents`` endpoints.

    Create, read, update, and delete document content and metadata.
    """

    def __init__(self, api: ApiClient) -> None:
        self._api = api

    def get(
        self,
        uri: str | list,
        *,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        timestamp: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Retrieve document content and/or metadata from the database.

        Documentation: https://docs.marklogic.com/REST/GET/v1/documents

        Parameters
        ----------
        uri : str | list
            One or more URIs for documents in the database.
            If you specify multiple URIs, the Accept header must be multipart/mixed.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The expected format of metadata returned in the response.
            Accepted values: xml or json.
            This parameter does not affect document content.
            For metadata, this parameter overrides the MIME type in the Accept header,
            except when the Accept header is multipart/mixed.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request. Use this parameter to fetch documents based on the contents
            of the database at a fixed point-in-time.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with document content and/or metadata

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
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
        return self._api.call(call, timeout=timeout)

    def head(
        self,
        uri: str,
        *,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        txid: str | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Get the headers a GET of one document's content or metadata would return.

        The response has no body: status 200 (OK) when the document exists and
        404 (Not Found) when it does not.

        Documentation: https://docs.marklogic.com/REST/HEAD/v1/documents

        Parameters
        ----------
        uri : str
            The URI of a document in the database. MarkLogic accepts a single URI
            per request.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data for which to generate headers. Category can be
            specified multiple times to request any combination of content
            and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The format of metadata whose headers are generated: xml or json.
            Content-only requests also accept text and binary without converting
            the stored content or changing its Content-Type.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response without a body, carrying the document's headers
            (Content-Type, vnd.marklogic.document-format, ML-Effective-Timestamp)

        Raises
        ------
        WrongParametersError
            If a category or format is unsupported, or a metadata request
            uses a format other than json or xml.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        call = DocumentsHeadCall(
            uri=uri,
            database=database,
            category=category,
            data_format=data_format,
            txid=txid,
        )
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        body_parts: list[DocumentsBodyPart],
        *,
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Insert or update content and/or metadata for multiple documents.

        Documentation: https://docs.marklogic.com/REST/POST/v1/documents

        Parameters
        ----------
        body_parts : list[DocumentsBodyPart]
            A list of multipart request body parts
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. Transforms are applied only to content
            parts: the transform is applied to the content of a part prior to
            updating or inserting the document.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        temporal_collection : str
            Specify the name of a temporal collection into which the documents are
            to be inserted.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``application/json`` body containing
            the write results

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        call = DocumentsPostCall(
            body_parts=body_parts,
            database=database,
            transform=transform,
            transform_params=transform_params,
            txid=txid,
            temporal_collection=temporal_collection,
            system_time=system_time,
        )
        return self._api.call(call, timeout=timeout)

    def delete(
        self,
        uri: str | list,
        *,
        database: str | None = None,
        category: str | list | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        wipe_temporal: bool | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Remove documents, or reset document metadata.

        Documentation: https://docs.marklogic.com/REST/DELETE/v1/documents

        Parameters
        ----------
        uri : str | list
            The URI of a document to delete or for which to remove metadata.
            You can specify multiple documents.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data to remove/reset.
            Category may be specified multiple times to remove or reset
            any combination of content and metadata.
            Valid categories: content (default), metadata, metadata-values,
            collections, permissions, properties, and quality.
            Use metadata to reset all metadata.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        temporal_collection : str
            Specify the name of a temporal collection that contains the document(s)
            to be deleted. Applies to all documents when deleting more than one.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.
            Applies to all documents when deleting more than one.
        wipe_temporal : bool
            Remove all versions of a temporal document rather than performing
            a temporal delete. You can only use this parameter when you also specify
            a temporal-collection parameter.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        WrongParametersError
            If a category, including an empty string, is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        call = DocumentsDeleteCall(
            uri=uri,
            database=database,
            category=category,
            txid=txid,
            temporal_collection=temporal_collection,
            system_time=system_time,
            wipe_temporal=wipe_temporal,
        )
        return self._api.call(call, timeout=timeout)


class AsyncDocumentsApi:
    """Async mid-level API for ``/v1/documents`` endpoints."""

    def __init__(self, api: AsyncApiClient) -> None:
        self._api = api

    async def get(
        self,
        uri: str | list,
        *,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        timestamp: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Retrieve document content and/or metadata from the database.

        Documentation: https://docs.marklogic.com/REST/GET/v1/documents

        Parameters
        ----------
        uri : str | list
            One or more URIs for documents in the database.
            If you specify multiple URIs, the Accept header must be multipart/mixed.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The expected format of metadata returned in the response.
            Accepted values: xml or json.
            This parameter does not affect document content.
            For metadata, this parameter overrides the MIME type in the Accept header,
            except when the Accept header is multipart/mixed.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request. Use this parameter to fetch documents based on the contents
            of the database at a fixed point-in-time.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with document content and/or metadata

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
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
        return await self._api.call(call, timeout=timeout)

    async def head(
        self,
        uri: str,
        *,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        txid: str | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Get the headers a GET of one document's content or metadata would return.

        The response has no body: status 200 (OK) when the document exists and
        404 (Not Found) when it does not.

        Documentation: https://docs.marklogic.com/REST/HEAD/v1/documents

        Parameters
        ----------
        uri : str
            The URI of a document in the database. MarkLogic accepts a single URI
            per request.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data for which to generate headers. Category can be
            specified multiple times to request any combination of content
            and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The format of metadata whose headers are generated: xml or json.
            Content-only requests also accept text and binary without converting
            the stored content or changing its Content-Type.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response without a body, carrying the document's headers
            (Content-Type, vnd.marklogic.document-format, ML-Effective-Timestamp)

        Raises
        ------
        WrongParametersError
            If a category or format is unsupported, or a metadata request
            uses a format other than json or xml.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        call = DocumentsHeadCall(
            uri=uri,
            database=database,
            category=category,
            data_format=data_format,
            txid=txid,
        )
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        body_parts: list[DocumentsBodyPart],
        *,
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Insert or update content and/or metadata for multiple documents.

        Documentation: https://docs.marklogic.com/REST/POST/v1/documents

        Parameters
        ----------
        body_parts : list[DocumentsBodyPart]
            A list of multipart request body parts
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. Transforms are applied only to content
            parts: the transform is applied to the content of a part prior to
            updating or inserting the document.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        temporal_collection : str
            Specify the name of a temporal collection into which the documents are
            to be inserted.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``application/json`` body containing
            the write results

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        call = DocumentsPostCall(
            body_parts=body_parts,
            database=database,
            transform=transform,
            transform_params=transform_params,
            txid=txid,
            temporal_collection=temporal_collection,
            system_time=system_time,
        )
        return await self._api.call(call, timeout=timeout)

    async def delete(
        self,
        uri: str | list,
        *,
        database: str | None = None,
        category: str | list | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        wipe_temporal: bool | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> Response:
        """Remove documents, or reset document metadata.

        Documentation: https://docs.marklogic.com/REST/DELETE/v1/documents

        Parameters
        ----------
        uri : str | list
            The URI of a document to delete or for which to remove metadata.
            You can specify multiple documents.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data to remove/reset.
            Category may be specified multiple times to remove or reset
            any combination of content and metadata.
            Valid categories: content (default), metadata, metadata-values,
            collections, permissions, properties, and quality.
            Use metadata to reset all metadata.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        temporal_collection : str
            Specify the name of a temporal collection that contains the document(s)
            to be deleted. Applies to all documents when deleting more than one.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.
            Applies to all documents when deleting more than one.
        wipe_temporal : bool
            Remove all versions of a temporal document rather than performing
            a temporal delete. You can only use this parameter when you also specify
            a temporal-collection parameter.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        WrongParametersError
            If a category, including an empty string, is not supported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        call = DocumentsDeleteCall(
            uri=uri,
            database=database,
            category=category,
            txid=txid,
            temporal_collection=temporal_collection,
            system_time=system_time,
            wipe_temporal=wipe_temporal,
        )
        return await self._api.call(call, timeout=timeout)
