"""The ML Documents Client module.

It exports high-level class to perform CRUD operations in aMarkLogic server:
    * DocumentsClient
        An MLResourceClient calling /v1/documents endpoint.
"""
from __future__ import annotations

from typing import Any, Iterator

from requests import Response

from mlclient import constants
from mlclient.calls import DocumentsGetCall
from mlclient.calls.model import (
    Category,
    ContentDispositionSerializer,
    DocumentsContentDisposition,
)
from mlclient.clients import MLResourceClient
from mlclient.exceptions import MarkLogicError
from mlclient.ml_response_parser import MLResponseParser
from mlclient.model import Document, DocumentFactory, Metadata


class DocumentsClient(MLResourceClient):
    """An MLResourceClient calling /v1/documents endpoint.

    It is a high-level class performing CRUD operations in a MarkLogic server.
    """

    def read(
        self,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list | None = None,
        database: str | None = None,
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
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        database : str | None, default None
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.

        Returns
        -------
        Document | list[Document]
            One or more documents from the database.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        call = self._get_call(uris=uris, category=category, database=database)
        resp = self.call(call)
        return self._parse(resp, uris, category)

    @classmethod
    def _get_call(
        cls,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list | None,
        database: str | None,
    ) -> DocumentsGetCall:
        """Prepare a DocumentsGetCall instance.

        It initializes an DocumentsGetCall instance with adjusted parameters. When
        the category param contains any metadata category, format is set to json.

        Parameters
        ----------
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : str | list | None, default None
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        database : str | None, default None
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.

        Returns
        -------
        DocumentsGetCall
            A prepared DocumentsGetCall instance
        """
        params = {
            "uri": uris,
            "category": category,
            "database": database,
        }
        if (
            category
            and category != "content"
            or isinstance(category, list)
            and category != ["content"]
        ):
            params["data_format"] = "json"

        return DocumentsGetCall(**params)

    @classmethod
    def _parse(
        cls,
        resp: Response,
        uris: str | list[str] | tuple[str] | set[str],
        category: str | list | None,
    ) -> Document | list[Document]:
        """Parse a MarkLogic response to Documents.

        Parameters
        ----------
        resp : Response
            A MarkLogic Server response
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : str | list | None
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.

        Returns
        -------
        Document | list[Document]
            A single Document instance or their list depending on uris type.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        parsed_resp = cls._parse_response(resp)
        content_type = resp.headers.get(constants.HEADER_NAME_CONTENT_TYPE)
        is_multipart = content_type.startswith(constants.HEADER_MULTIPART_MIXED)
        documents_data = cls._pre_format_data(parsed_resp, is_multipart, uris, category)
        docs = cls._parse_to_documents(documents_data)
        if isinstance(uris, str):
            return docs[0]
        return docs

    @classmethod
    def _parse_response(
        cls,
        resp: Response,
    ) -> list[tuple]:
        """Parse a response from a MarkLogic server.

        Parameters
        ----------
        resp : Response
            A MarkLogic Server response

        Returns
        -------
        list[tuple]
            A parsed response parts with headers

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        if not resp.ok:
            resp_body = resp.json()
            raise MarkLogicError(resp_body["errorResponse"])
        parsed_resp = MLResponseParser.parse_with_headers(resp)
        if isinstance(parsed_resp, tuple):
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
        """Prepare data to initialize Document instances.

        Parameters
        ----------
        parsed_resp : list[tuple]
            A parsed MarkLogic response parts with headers
        is_multipart : bool
            A flag informing whether the response is multipart/mixed or not
        uris : str | list[str] | tuple[str] | set[str]
            One or more URIs for documents in the database.
        category : str | list | None
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.

        Returns
        -------
        Iterator[dict]
            An iterator of pre-formatted data in form of dictionaries
        """
        if is_multipart:
            return cls._pre_format_documents(parsed_resp, category)
        return cls._pre_format_document(parsed_resp, uris, category)

    @classmethod
    def _pre_format_documents(
        cls,
        parsed_resp: list[tuple],
        origin_category: str | list | None,
    ) -> Iterator[dict]:
        """Prepare document parts to initialize Document instances.

        Parameters
        ----------
        parsed_resp : list[tuple]
            A parsed MarkLogic response parts with headers
        origin_category : str | list | None
            Categories provided by the user

        Returns
        -------
        Iterator[dict]
            An iterator of pre-formatted data in form of dictionaries
        """
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
            else:
                data = pre_formatted_data[content_disp.filename]
                if content_disp.category == Category.CONTENT:
                    data.update(partial_data)
                    yield data
                else:
                    partial_data.update(data)
                    yield partial_data

    @classmethod
    def _pre_format_document(
        cls,
        parsed_resp: list[tuple],
        origin_uris: str | list[str] | tuple[str] | set[str],
        origin_category: str | list | None,
    ) -> Iterator[dict]:
        """Prepare a single-part document to initialize Document instances.

        Parameters
        ----------
        parsed_resp : list[tuple]
            A parsed MarkLogic response parts with headers
        origin_uris
            Uris provided by the user
        origin_category : str | list | None
            Categories provided by the user

        Returns
        -------
        Iterator[dict]
            An iterator of pre-formatted data in form of dictionaries
        """
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
                "metadata": cls._parse_metadata(parsed_resp_body),
            }

    @classmethod
    def _expect_categories(
        cls,
        origin_category: str | list | None,
    ) -> tuple[bool, bool]:
        """Return expectation flags based on categories sent by a user.

        Parameters
        ----------
        origin_category : str | list | None
            Categories provided by the user

        Returns
        -------
        tuple[bool, bool]
            Expectation flags informing whether data should contain content
            and/or metadata.
        """
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
        """Return pre-formatted partial data.

        Parameters
        ----------
        content_disp : DocumentsContentDisposition
            A content disposition of a response part
        parsed_resp_body : Any
            A parsed response part

        Returns
        -------
        dict
            Pre-formatted data in form of a dictionary
        """
        if content_disp.category == Category.CONTENT:
            return {
                "uri": content_disp.filename,
                "format": content_disp.format_,
                "content": parsed_resp_body,
            }
        return {
            "uri": content_disp.filename,
            "metadata": cls._parse_metadata(parsed_resp_body),
        }

    @classmethod
    def _parse_metadata(
        cls,
        raw_metadata: dict,
    ) -> Metadata:
        """Parse metadata from a response to a Metadata instance.

        Parameters
        ----------
        raw_metadata : dict
            A raw metadata returned by a MarkLogic server

        Returns
        -------
        Metadata
            A parsed Metadata instance.
        """
        if "metadataValues" in raw_metadata:
            raw_metadata["metadata_values"] = raw_metadata["metadataValues"]
            del raw_metadata["metadataValues"]

        return Metadata(**raw_metadata)

    @classmethod
    def _parse_to_documents(
        cls,
        documents_data: Iterator[dict],
    ) -> list[Document]:
        """Parse pre-formatted data to a list of Document instances.

        Parameters
        ----------
        documents_data : Iterator[dict]
            An iterator of pre-formatted data in form of dictionaries

        Returns
        -------
        list[Document]
            A list of parsed Document instances
        """
        return [
            cls._parse_to_document(document_data) for document_data in documents_data
        ]

    @classmethod
    def _parse_to_document(
        cls,
        document_data: dict,
    ) -> Document:
        """Parse pre-formatted data to a Document instance.

        Parameters
        ----------
        document_data : dict
            Pre-formatted data in form of a dictionary

        Returns
        -------
        Document
            A parsed Document instance
        """
        uri = document_data.get("uri")
        doc_format = document_data.get("format")
        content = document_data.get("content")
        metadata = document_data.get("metadata")
        return DocumentFactory.build_document(
            content=content,
            doc_type=doc_format,
            uri=uri,
            metadata=metadata,
        )
