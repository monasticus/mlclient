"""Parse multi-document reads into Document models for the services.

Document reads and REST search both return documents as multipart/mixed
responses; this module turns them into Document instances.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from mlclient import _constants as constants
from mlclient.models.document_parts import Category, DocumentsDisposition
from mlclient.models.documents import Document, Metadata
from mlclient.responses import MLResponseParser

if TYPE_CHECKING:
    from httpx import Response


def normalize_category(
    category: Category | str | list[Category | str] | None,
) -> str | list[str] | None:
    """Normalize category values from Category enums to strings.

    Parameters
    ----------
    category : Category | str | list[Category | str] | None
        One category or several, as enums or their string values.

    Returns
    -------
    str | list[str] | None
        The same categories as strings; None stays None.
    """
    if category is None:
        return None
    if isinstance(category, list):
        return [c.value if isinstance(c, Category) else c for c in category]
    if isinstance(category, Category):
        return category.value
    return category


class DocumentsReader:
    """Parse MarkLogic document read responses into Document instances."""

    @classmethod
    def parse(
        cls,
        resp: Response,
        category: str | list[str] | None,
        *,
        uris: str | list[str] | tuple[str] | set[str] | None = None,
    ) -> Iterator[Document]:
        """Parse a single-document or multipart/mixed response to Documents.

        Parameters
        ----------
        resp : Response
            The MarkLogic response.
        category : str | list[str] | None
            The categories requested; None means content only.
        uris : str | list[str] | tuple[str] | set[str] | None, default None
            The requested URIs; a single-document response carries no URI, so
            it takes the first one. Multipart responses name every part.

        Returns
        -------
        Iterator[Document]
            The documents in response order.
        """
        parsed_resp = cls._parse_response(resp)
        content_type = resp.headers.get(constants.HEADER_NAME_CONTENT_TYPE)
        is_multipart = content_type.startswith(constants.HEADER_MULTIPART_MIXED)
        documents_data = cls._pre_format_data(parsed_resp, is_multipart, uris, category)
        return cls._parse_to_documents(documents_data)

    @classmethod
    def _parse_response(
        cls,
        resp: Response,
    ) -> list[tuple]:
        """Split a response into header and body pairs.

        Parameters
        ----------
        resp : Response
            The MarkLogic response.

        Returns
        -------
        list[tuple]
            One ``(headers, body)`` pair per part; [] for an empty body.
        """
        parsed_resp = MLResponseParser.parse_with_headers(resp, output_type=bytes)
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
        uris: str | list[str] | tuple[str] | set[str] | None,
        category: str | list[str] | None,
    ) -> Iterator[dict]:
        """Prepare document data from multipart or single-document parts.

        Parameters
        ----------
        parsed_resp : list[tuple]
            The ``(headers, body)`` pairs.
        is_multipart : bool
            Whether the response is multipart/mixed.
        uris : str | list[str] | tuple[str] | set[str] | None
            The requested URIs, used only for a single-document response.
        category : str | list[str] | None
            The categories requested.

        Returns
        -------
        Iterator[dict]
            Keyword data for one Document each.
        """
        if is_multipart:
            return cls._pre_format_documents(parsed_resp, category)
        return cls._pre_format_document(parsed_resp, uris, category)

    @classmethod
    def _pre_format_documents(
        cls,
        parsed_resp: list[tuple],
        origin_category: str | list[str] | None,
    ) -> Iterator[dict]:
        """Merge the content and metadata parts of each multipart document.

        Parameters
        ----------
        parsed_resp : list[tuple]
            The ``(headers, body)`` pairs.
        origin_category : str | list[str] | None
            The categories requested.

        Returns
        -------
        Iterator[dict]
            Keyword data for one Document each, once all its parts are read.
        """
        expect_content, expect_metadata = cls._expect_categories(origin_category)
        pre_formatted_data = {}
        for headers, parse_resp_body in parsed_resp:
            raw_content_disp = headers.get(constants.HEADER_NAME_CONTENT_DISP)
            content_disp = DocumentsDisposition.from_header(raw_content_disp)
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
        origin_uris: str | list[str] | tuple[str] | set[str] | None,
        origin_category: str | list[str] | None,
    ) -> Iterator[dict]:
        """Prepare a single-document response, named by the requested URI.

        Parameters
        ----------
        parsed_resp : list[tuple]
            The single ``(headers, body)`` pair.
        origin_uris : str | list[str] | tuple[str] | set[str] | None
            The requested URI, or a list whose first item is used.
        origin_category : str | list[str] | None
            The categories requested.

        Returns
        -------
        Iterator[dict]
            Keyword data for the one Document.
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
                "metadata": cls._pre_format_metadata(parsed_resp_body),
            }

    @classmethod
    def _pre_format_metadata(
        cls,
        raw_metadata: bytes | str,
    ) -> bytes | str:
        """Return raw metadata unchanged, for Metadata to parse lazily.

        Parameters
        ----------
        raw_metadata : bytes | str
            The metadata part's body.

        Returns
        -------
        bytes | str
            The same metadata.
        """
        return raw_metadata

    @classmethod
    def _expect_categories(
        cls,
        origin_category: str | list[str] | None,
    ) -> tuple[bool, bool]:
        """Return which parts the requested categories make MarkLogic send.

        Parameters
        ----------
        origin_category : str | list[str] | None
            The categories requested; None means content only.

        Returns
        -------
        tuple[bool, bool]
            Whether content parts and whether metadata parts are expected.
        """
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
        content_disp: DocumentsDisposition,
        parsed_resp_body: Any,
    ) -> dict:
        """Return the data one multipart part contributes to its Document.

        Parameters
        ----------
        content_disp : DocumentsDisposition
            The part's parsed Content-Disposition.
        parsed_resp_body : Any
            The part's body.

        Returns
        -------
        dict
            The URI with either format and content or metadata.
        """
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
    ) -> Iterator[Document]:
        """Create a Document from each prepared data item.

        Parameters
        ----------
        documents_data : Iterator[dict]
            Prepared keyword data.

        Returns
        -------
        Iterator[Document]
            One Document per item.
        """
        for document_data in documents_data:
            yield cls._parse_to_document(document_data)

    @classmethod
    def _parse_to_document(
        cls,
        document_data: dict,
    ) -> Document:
        """Create a Document, or a metadata-only update without content.

        Parameters
        ----------
        document_data : dict
            Prepared keyword data: uri, and format and content or metadata.

        Returns
        -------
        Document
            The parsed document.
        """
        uri = document_data.get("uri")
        doc_format = document_data.get("format")
        content = document_data.get("content")
        raw_metadata = document_data.get("metadata")

        metadata = Metadata(raw=raw_metadata) if raw_metadata else None

        if content is None:
            return Document.metadata_update(uri, metadata or Metadata())

        return Document.create(
            content=content,
            doc_type=doc_format,
            uri=uri,
            metadata=metadata,
        )
