"""DocumentsApi - mid-level access to MarkLogic documents endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import DocumentsDeleteCall, DocumentsGetCall, DocumentsPostCall
from mlclient.models.http import DocumentsBodyPart as BodyPart

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient


class DocumentsApi:
    """Mid-level API for ``/v1/documents`` endpoints.

    Create, read, update, and delete document content and metadata.
    """

    def __init__(self, client: ApiClient):
        self._client = client

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

        Returns
        -------
        Response
            An HTTP response with document content and/or metadata
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
        return self._client.call(call)

    def post(
        self,
        body_parts: list[BodyPart],
        *,
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
    ) -> Response:
        """Insert or update content and/or metadata for multiple documents.

        Documentation: https://docs.marklogic.com/REST/POST/v1/documents

        Parameters
        ----------
        body_parts : list[BodyPart]
            A list of multipart request body parts
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
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
        temporal_collection : str
            Specify the name of a temporal collection into which the documents are
            to be inserted.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.

        Returns
        -------
        Response
            An HTTP response with ``application/json`` body containing
            the write results
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
        return self._client.call(call)

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

        Returns
        -------
        Response
            An HTTP response
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
        return self._client.call(call)
