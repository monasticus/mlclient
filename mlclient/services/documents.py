"""High-level Documents service.

Provides parsed document operations on MarkLogic.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from httpx import Response

from mlclient import constants
from mlclient.calls import DocumentsDeleteCall, DocumentsGetCall, DocumentsPostCall
from mlclient.exceptions import MarkLogicError
from mlclient.mimetypes import Mimetypes
from mlclient.ml_response_parser import MLResponseParser
from mlclient.structures import (
    Document,
    DocumentFactory,
    Metadata,
    MetadataDocument,
    RawDocument,
    RawStringDocument,
)
from mlclient.structures.calls import (
    Category,
    ContentDispositionSerializer,
    DocumentsBodyPart,
    DocumentsContentDisposition,
)

from mlclient.clients.rest_client import RestClient


class DocumentsService:
    """High-level service for /v1/documents CRUD operations."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def create(
        self,
        data: Document | Metadata | list[Document | Metadata],
        database: str | None = None,
        temporal_collection: str | None = None,
    ) -> dict:
        """Create or update document(s) content or metadata.

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
        resp = self._rest.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
        return MLResponseParser.parse(resp)

    def read(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list | None = None,
        database: str | None = None,
        output_type: type | None = None,
    ) -> Document | list[Document]:
        """Return document(s) content or metadata from a MarkLogic database.

        When uris is a string it returns a single Document instance. Otherwise,
        result is a list.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : str | list | None, default None
            The category of data to fetch about the requested document.
        database : str | None, default None
            Perform this operation on the named content database.
        output_type : type | None, default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        Document | list[Document]
            One or more documents from the database.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        call = DocumentsGetCall(
            uri=uris,
            category=category,
            database=database,
            data_format="json",
        )
        resp = self._rest.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])
        return DocumentsReader.parse(resp, uris, category, output_type)

    def delete(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list | None = None,
        database: str | None = None,
        temporal_collection: str | None = None,
        wipe_temporal: bool | None = None,
    ):
        """Delete document(s) content or metadata in a MarkLogic database.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            The URI of a document to delete.
        category : str | list | None, default None
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
        call = DocumentsDeleteCall(
            uri=uris,
            category=category,
            database=database,
            temporal_collection=temporal_collection,
            wipe_temporal=wipe_temporal,
        )
        resp = self._rest.call(call)
        if not resp.is_success:
            resp_body = MLResponseParser.parse(resp)
            raise MarkLogicError(resp_body["errorResponse"])


class DocumentsSender:
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
                    "body_part_type": "attachment",
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
        metadata = document.metadata
        if type(document) not in (RawDocument, RawStringDocument):
            metadata = metadata.to_json_string()
        return DocumentsBodyPart(
            **{
                "content-type": constants.HEADER_JSON,
                "content-disposition": {
                    "body_part_type": "attachment",
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
    ) -> DocumentsBodyPart:
        """Instantiate DocumentsBodyPart with default metadata."""
        metadata = metadata.to_json_string()
        return DocumentsBodyPart(
            **{
                "content-type": constants.HEADER_JSON,
                "content-disposition": {
                    "body_part_type": "inline",
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
        category: str | list | None,
        output_type: type | None = None,
    ) -> Document | list[Document]:
        """Parse a MarkLogic response to Documents."""
        parsed_resp = cls._parse_response(resp, output_type)
        content_type = resp.headers.get(constants.HEADER_NAME_CONTENT_TYPE)
        is_multipart = content_type.startswith(constants.HEADER_MULTIPART_MIXED)
        documents_data = cls._pre_format_data(parsed_resp, is_multipart, uris, category)
        docs = cls._parse_to_documents(documents_data, output_type)
        if isinstance(uris, str):
            return docs[0]
        return docs

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
        category: str | list | None,
    ) -> Iterator[dict]:
        """Prepare data to initialize Document instances."""
        if is_multipart:
            return cls._pre_format_documents(parsed_resp, category)
        return cls._pre_format_document(parsed_resp, uris, category)

    @classmethod
    def _pre_format_documents(
        cls,
        parsed_resp: list[tuple],
        origin_category: str | list | None,
    ) -> Iterator[dict]:
        """Prepare document parts to initialize Document instances."""
        expect_content, expect_metadata = cls._expect_categories(origin_category)
        pre_formatted_data = {}
        for headers, parse_resp_body in parsed_resp:
            raw_content_disp = headers.get(constants.HEADER_NAME_CONTENT_DISP)
            content_disp = ContentDispositionSerializer.serialize(raw_content_disp)
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
        origin_category: str | list | None,
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
        origin_category: str | list | None,
    ) -> tuple[bool, bool]:
        """Return expectation flags based on categories sent by a user."""
        expect_content = (
            not origin_category or Category.CONTENT.value in origin_category
        )
        expect_metadata = origin_category and any(
            cat.value in origin_category for cat in Category if cat != cat.CONTENT
        )
        return expect_content, expect_metadata

    @classmethod
    def _get_partial_data(
        cls,
        content_disp: DocumentsContentDisposition,
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
    ) -> list[Document]:
        """Parse pre-formatted data to a list of Document instances."""
        return [
            cls._parse_to_document(document_data, output_type)
            for document_data in documents_data
        ]

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
            factory_function = DocumentFactory.build_raw_document
        else:
            metadata = Metadata(**metadata) if metadata else metadata
            factory_function = DocumentFactory.build_document

        return factory_function(
            content=content,
            doc_type=doc_format,
            uri=uri,
            metadata=metadata,
        )
