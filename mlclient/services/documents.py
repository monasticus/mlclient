"""High-level Documents service (DocumentsService / AsyncDocumentsService).

Provides parsed document operations on MarkLogic.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from httpx import Response

from mlclient import constants
from mlclient.calls import DocumentsDeleteCall, DocumentsGetCall, DocumentsPostCall
from mlclient.clients.api_client import ApiClient
from mlclient.exceptions import MarkLogicError

if TYPE_CHECKING:
    from mlclient.clients.api_client import AsyncApiClient

from mlclient.mimetypes import Mimetypes
from mlclient.ml_response_parser import MLResponseParser
from mlclient.models import (
    Document,
    Metadata,
    MetadataDocument,
    RawDocument,
    RawStringDocument,
)
from mlclient.models.http import Category
from mlclient.models.http import DocumentsBodyPart as BodyPart
from mlclient.models.http import DocumentsDisposition as Disposition


def _normalize_category(
    category: Category | str | list[Category | str] | None,
) -> str | list[str] | None:
    """Normalize category values from Category enums to strings."""
    if category is None:
        return None
    if isinstance(category, list):
        return [c.value if isinstance(c, Category) else c for c in category]
    if isinstance(category, Category):
        return category.value
    return category


class DocumentsService:
    """High-level service for /v1/documents CRUD operations.

    Notes
    -----
    MarkLogic's REST API (App-Services, port 8000) and Manage API (port 8002)
    return different HTTP status codes for the same underlying errors. For
    example, RESTAPI-NODOCUMENT and XDMP-DOCNOTFOUND are returned as
    **404 Not Found** on the REST API but as **500 Internal Server Error**
    on the Manage API. This is due to different error handler mappings on
    each port.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def write(
        self,
        data: Document | Metadata | list[Document | Metadata],
        *,
        database: str | None = None,
        temporal_collection: str | None = None,
    ) -> dict:
        """Write (create or update) document(s) content or metadata.

        Parameters
        ----------
        data : Document | Metadata | list[Document | Metadata]
            One or more document or default metadata.
        database : str | None, default None
            Perform this operation on the named content database.
        temporal_collection : str | None, default None
            Temporal collection name.

        Returns
        -------
        dict
            An origin response from a MarkLogic server.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        body_parts = DocumentsSender.parse(data)
        call = DocumentsPostCall(
            body_parts=body_parts,
            database=database,
            temporal_collection=temporal_collection,
        )
        resp = self._api.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
        return MLResponseParser.parse(resp)

    def read(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = None,
        output_type: type | None = None,
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
        database : str | None, default None
            Perform this operation on the named content database.
        output_type : type | None, default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        Document | dict[str, Document]
            A single document when uris is a string, otherwise a dict keyed by URI.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        docs = self.read_stream(
            uris,
            category=category,
            database=database,
            output_type=output_type,
        )
        return next(docs) if isinstance(uris, str) else {doc.uri: doc for doc in docs}

    def read_stream(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = None,
        output_type: type | None = None,
    ) -> Iterator[Document]:
        """Return document(s) as an iterator, suitable for batch processing.

        Unlike read(), does not materialize results into a dict.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : Category | str | list[Category | str] | None, default None
            The category of data to fetch about the requested document.
        database : str | None, default None
            Perform this operation on the named content database.
        output_type : type | None, default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        Iterator[Document]
            Documents from the database.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        category = _normalize_category(category)
        call = DocumentsGetCall(
            uri=uris,
            category=category,
            database=database,
            data_format="json",
        )
        resp = self._api.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
        return DocumentsReader.parse(resp, uris, category, output_type)

    def delete(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = None,
        temporal_collection: str | None = None,
        wipe_temporal: bool | None = None,
    ):
        """Delete document(s) content or metadata in a MarkLogic database.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            The URI of a document to delete.
        category : Category | str | list[Category | str] | None, default None
            The category of data to remove/reset.
        database : str | None, default None
            Perform this operation on the named content database.
        temporal_collection : str | None, default None
            Temporal collection name.
        wipe_temporal : bool | None, default None
            Remove all versions of a temporal document.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        category = _normalize_category(category)
        call = DocumentsDeleteCall(
            uri=uris,
            category=category,
            database=database,
            temporal_collection=temporal_collection,
            wipe_temporal=wipe_temporal,
        )
        resp = self._api.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])


class DocumentsSender:
    """A class parsing Document or Metadata instance(s) to BodyPart's list."""

    @classmethod
    def parse(
        cls,
        data: Document | Metadata | list[Document | Metadata],
    ) -> list[BodyPart]:
        """Parse Document or Metadata instance(s) to BodyPart's list."""
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
    ) -> BodyPart:
        """Instantiate BodyPart with Document's content."""
        return BodyPart(
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
    ) -> BodyPart:
        """Instantiate BodyPart with Document's metadata."""
        metadata = document.metadata
        if type(document) not in (RawDocument, RawStringDocument):
            metadata = metadata.to_json_string()
        return BodyPart(
            **{
                "content-type": constants.HEADER_JSON,
                "content-disposition": {
                    "type": "attachment",
                    "filename": document.uri,
                    "category": "metadata",
                },
                "content": metadata,
            },
        )

    @classmethod
    def _get_default_metadata_body_part(
        cls,
        metadata: Metadata,
    ) -> BodyPart:
        """Instantiate BodyPart with default metadata."""
        metadata = metadata.to_json_string()
        return BodyPart(
            **{
                "content-type": constants.HEADER_JSON,
                "content-disposition": {
                    "type": "inline",
                    "category": "metadata",
                },
                "content": metadata,
            },
        )


class DocumentsReader:
    """A class parsing raw MarkLogic response to Document instance(s)."""

    @classmethod
    def parse(
        cls,
        resp: Response,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list[str] | None,
        output_type: type | None = None,
    ) -> Iterator[Document]:
        """Parse a MarkLogic response to Documents."""
        parsed_resp = cls._parse_response(resp, output_type)
        content_type = resp.headers.get(constants.HEADER_NAME_CONTENT_TYPE)
        is_multipart = content_type.startswith(constants.HEADER_MULTIPART_MIXED)
        documents_data = cls._pre_format_data(parsed_resp, is_multipart, uris, category)
        return cls._parse_to_documents(documents_data, output_type)

    @classmethod
    def _parse_response(
        cls,
        resp: Response,
        output_type: type | None,
    ) -> list[tuple]:
        """Parse a response from a MarkLogic server."""
        parsed_resp = MLResponseParser.parse_with_headers(resp, output_type)
        if not isinstance(parsed_resp, list):
            headers, _ = parsed_resp
            if headers.get(constants.HEADER_NAME_CONTENT_LENGTH) == "0":
                return []
            return [parsed_resp]
        return parsed_resp

    @classmethod
    def _pre_format_data(
        cls,
        parsed_resp: list[tuple],
        is_multipart: bool,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list[str] | None,
    ) -> Iterator[dict]:
        """Prepare data to initialize Document instances."""
        if is_multipart:
            return cls._pre_format_documents(parsed_resp, category)
        return cls._pre_format_document(parsed_resp, uris, category)

    @classmethod
    def _pre_format_documents(
        cls,
        parsed_resp: list[tuple],
        origin_category: str | list[str] | None,
    ) -> Iterator[dict]:
        """Prepare document parts to initialize Document instances."""
        expect_content, expect_metadata = cls._expect_categories(origin_category)
        pre_formatted_data = {}
        for headers, parse_resp_body in parsed_resp:
            raw_content_disp = headers.get(constants.HEADER_NAME_CONTENT_DISP)
            content_disp = Disposition.from_header(raw_content_disp)
            partial_data = cls._get_partial_data(content_disp, parse_resp_body)

            if not (expect_content and expect_metadata):
                yield partial_data
            elif content_disp.filename not in pre_formatted_data:
                pre_formatted_data[content_disp.filename] = partial_data
            elif content_disp.category == Category.CONTENT:
                pre_formatted_data[content_disp.filename].update(partial_data)
                yield pre_formatted_data[content_disp.filename]
            else:
                partial_data.update(pre_formatted_data[content_disp.filename])
                yield partial_data

    @classmethod
    def _pre_format_document(
        cls,
        parsed_resp: list[tuple],
        origin_uris: str | list[str] | tuple[str] | set[str],
        origin_category: str | list[str] | None,
    ) -> Iterator[dict]:
        """Prepare a single-part document to initialize Document instances."""
        headers, parsed_resp_body = parsed_resp[0]
        uri = origin_uris[0] if isinstance(origin_uris, list) else origin_uris
        expect_content, _ = cls._expect_categories(origin_category)
        if expect_content:
            yield {
                "uri": uri,
                "format": headers.get(constants.HEADER_NAME_ML_DOCUMENT_FORMAT),
                "content": parsed_resp_body,
            }
        else:
            yield {
                "uri": uri,
                "metadata": cls._pre_format_metadata(parsed_resp_body),
            }

    @classmethod
    def _pre_format_metadata(
        cls,
        raw_metadata: dict | bytes | str,
    ) -> dict | bytes | str:
        """Prepare raw metadata from a MarkLogic server response."""
        if isinstance(raw_metadata, dict) and "metadataValues" in raw_metadata:
            raw_metadata["metadata_values"] = raw_metadata["metadataValues"]
            del raw_metadata["metadataValues"]
        return raw_metadata

    @classmethod
    def _expect_categories(
        cls,
        origin_category: str | list[str] | None,
    ) -> tuple[bool, bool]:
        """Return expectation flags based on categories sent by a user."""
        expect_content = (
            not origin_category or Category.CONTENT.value in origin_category
        )
        expect_metadata = origin_category and any(
            cat.value in origin_category for cat in Category if cat != Category.CONTENT
        )
        return expect_content, expect_metadata

    @classmethod
    def _get_partial_data(
        cls,
        content_disp: Disposition,
        parsed_resp_body: Any,
    ) -> dict:
        """Return pre-formatted partial data."""
        if content_disp.category == Category.CONTENT:
            return {
                "uri": content_disp.filename,
                "format": content_disp.format_,
                "content": parsed_resp_body,
            }
        return {
            "uri": content_disp.filename,
            "metadata": cls._pre_format_metadata(parsed_resp_body),
        }

    @classmethod
    def _parse_to_documents(
        cls,
        documents_data: Iterator[dict],
        output_type: type | None,
    ) -> Iterator[Document]:
        """Parse pre-formatted data to Document instances."""
        for document_data in documents_data:
            yield cls._parse_to_document(document_data, output_type)

    @classmethod
    def _parse_to_document(
        cls,
        document_data: dict,
        output_type: type | None,
    ) -> Document:
        """Parse pre-formatted data to a Document instance."""
        uri = document_data.get("uri")
        doc_format = document_data.get("format")
        content = document_data.get("content")
        metadata = document_data.get("metadata")

        if output_type in (bytes, str):
            factory_function = Document.create_raw
        else:
            metadata = Metadata(**metadata) if metadata else metadata
            factory_function = Document.create

        return factory_function(
            content=content,
            doc_type=doc_format,
            uri=uri,
            metadata=metadata,
        )


class AsyncDocumentsService:
    """Async high-level service for /v1/documents CRUD operations."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def write(
        self,
        data: Document | Metadata | list[Document | Metadata],
        *,
        database: str | None = None,
        temporal_collection: str | None = None,
    ) -> dict:
        """Write documents to MarkLogic."""
        body_parts = DocumentsSender.parse(data)
        call = DocumentsPostCall(
            body_parts=body_parts,
            database=database,
            temporal_collection=temporal_collection,
        )
        resp = await self._api.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
        return MLResponseParser.parse(resp)

    async def read(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = None,
        output_type: type | None = None,
    ) -> Document | dict[str, Document]:
        """Read documents from MarkLogic."""
        docs = await self.read_stream(
            uris,
            category=category,
            database=database,
            output_type=output_type,
        )
        return next(docs) if isinstance(uris, str) else {doc.uri: doc for doc in docs}

    async def read_stream(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = None,
        output_type: type | None = None,
    ) -> Iterator[Document]:
        """Read documents from MarkLogic as a stream."""
        category = _normalize_category(category)
        call = DocumentsGetCall(
            uri=uris,
            category=category,
            database=database,
            data_format="json",
        )
        resp = await self._api.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
        return DocumentsReader.parse(resp, uris, category, output_type)

    async def delete(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        *,
        category: Category | str | list[Category | str] | None = None,
        database: str | None = None,
        temporal_collection: str | None = None,
        wipe_temporal: bool | None = None,
    ):
        """Delete documents from MarkLogic."""
        category = _normalize_category(category)
        call = DocumentsDeleteCall(
            uri=uris,
            category=category,
            database=database,
            temporal_collection=temporal_collection,
            wipe_temporal=wipe_temporal,
        )
        resp = await self._api.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
