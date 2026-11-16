"""The ML Response Parser module.

It exports 1 class:
    * MLResponseParser
        A MarkLogic HTTP response parser.
"""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ElemTree
from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar

from httpx import Headers, Response

from mlclient import _constants as const
from mlclient.exceptions import MarkLogicError
from mlclient.models.mimetypes import Mimetypes
from mlclient.models.results import ParsedValue
from mlclient.models.types import DocumentType
from mlclient.multipart import MultipartPart, decode_multipart_mixed

logger = logging.getLogger(__name__)


_FRACTIONAL_SECONDS = re.compile(r"(T\d{2}:\d{2}:\d{2})\.(\d+)")


def _parse_date_time(lexical: str) -> datetime:
    """Convert an xs:dateTime lexical form, whatever its fraction length.

    MarkLogic writes the canonical form, which drops trailing zeros from the
    fractional seconds (``.5``, ``.12345``); Python 3.10 parses only 3 or 6
    digits, so the fraction is padded, or truncated beyond microseconds.

    Parameters
    ----------
    lexical : str
        The xs:dateTime value, with ``Z`` or an offset, or none.

    Returns
    -------
    datetime
        The value, timezone-aware when the lexical form has a zone.
    """
    normalized = _FRACTIONAL_SECONDS.sub(
        lambda match: f"{match.group(1)}.{match.group(2)[:6].ljust(6, '0')}",
        lexical,
    )
    return datetime.fromisoformat(normalized.replace("Z", "+00:00"))


class MLResponseParser:
    """A MarkLogic HTTP response parser.

    MarkLogic returns responses with multipart/mixed content. This class allows to get
    all returned parts as python representations. They are parsed depending on content
    type of corresponding part.

    Examples
    --------
    >>> from mlclient import MLClient, MLResponseParser
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8002,
    ...     "username": "admin",
    ...     "password": "admin",
    ...     "auth": "digest",
    ... }
    >>> with MLClient(**config) as ml:
    ...     resp = ml.rest.eval.post(xquery="xdmp:database() => xdmp:database-name()")
    ...     print("Raw:", resp.text)
    ...     print("Parsed:", MLResponseParser.parse(resp))
    ...
    Raw:
    --6a5df7d535c71968
    Content-Type: text/plain
    X-Primitive: string
    App-Services
    --6a5df7d535c71968--
    Parsed: App-Services
    """

    _PLAIN_TEXT_PARSERS: ClassVar[dict] = {
        None: lambda data: data,
        const.HEADER_PRIMITIVE_STRING: lambda data: data,
        const.HEADER_PRIMITIVE_TEXT: str,
        const.HEADER_PRIMITIVE_ATTRIBUTE: str,
        const.HEADER_PRIMITIVE_COMMENT: str,
        const.HEADER_PRIMITIVE_PROCESSING_INSTRUCTION: str,
        const.HEADER_PRIMITIVE_BOOLEAN: lambda data: data in ("true", "1"),
        const.HEADER_PRIMITIVE_INTEGER: int,
        const.HEADER_PRIMITIVE_BYTE: int,
        const.HEADER_PRIMITIVE_SHORT: int,
        const.HEADER_PRIMITIVE_INT: int,
        const.HEADER_PRIMITIVE_LONG: int,
        const.HEADER_PRIMITIVE_NON_POSITIVE_INTEGER: int,
        const.HEADER_PRIMITIVE_NEGATIVE_INTEGER: int,
        const.HEADER_PRIMITIVE_NON_NEGATIVE_INTEGER: int,
        const.HEADER_PRIMITIVE_POSITIVE_INTEGER: int,
        const.HEADER_PRIMITIVE_UNSIGNED_BYTE: int,
        const.HEADER_PRIMITIVE_UNSIGNED_SHORT: int,
        const.HEADER_PRIMITIVE_UNSIGNED_INT: int,
        const.HEADER_PRIMITIVE_UNSIGNED_LONG: int,
        const.HEADER_PRIMITIVE_DECIMAL: Decimal,
        const.HEADER_PRIMITIVE_DOUBLE: float,
        const.HEADER_PRIMITIVE_FLOAT: float,
        const.HEADER_PRIMITIVE_DATE: lambda data: date.fromisoformat(data[:10]),
        const.HEADER_PRIMITIVE_DATE_TIME: _parse_date_time,
    }

    @classmethod
    def parse(
        cls,
        response: Response,
        output_type: type | None = None,
    ) -> ParsedValue:
        """Parse MarkLogic HTTP Response.

        The result follows the number of parts in the body, not its content
        type. A plain body (e.g. Manage JSON) gives one value. A multipart body
        gives a list, except that a multipart with a single part is unwrapped
        to its item, so calls expecting one answer (an eval returning one
        value, a documents read of one document) stay simple. An empty body
        gives ``[]``. Code iterating over a multipart result whose item count
        varies must handle a single item and ``[]`` as well as a list.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance
        output_type : type | None , default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        ParsedValue
            A parsed response body. xs:decimal retains precision as Decimal;
            xs:float and xs:double become float. Empty results return [],
            singletons return their item, and multiple items return a list.

        Raises
        ------
        MarkLogicError
            If MarkLogic answered a non-success status with an error it described
        HTTPStatusError
            If a non-success status carried no MarkLogic error body
        """
        cls.raise_for_status(response)
        logger.debug("Attempt to parse a response")
        if not response.content:
            logger.fine("No content to parse")
            return []
        return cls._parse(response, output_type)

    @classmethod
    def parse_with_headers(
        cls,
        response: Response,
        output_type: type | None = None,
    ) -> tuple | list[tuple]:
        """Parse MarkLogic HTTP Response and get headers.

        The result follows the number of parts in the body, like ``parse()``:
        a plain body or a multipart with a single part gives one
        ``(headers, value)`` tuple, a multipart with several parts gives a list
        of them, and an empty body gives ``(headers, [])``. Code iterating over
        a multipart result whose part count varies must handle a single tuple
        as well as a list.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance
        output_type : type | None , default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        tuple | list[tuple]
            A parsed response body with headers, one tuple per part

        Raises
        ------
        MarkLogicError
            If MarkLogic answered a non-success status with an error it described
        HTTPStatusError
            If a non-success status carried no MarkLogic error body
        """
        cls.raise_for_status(response)
        logger.debug("Attempt to parse a response")
        if not response.content:
            logger.fine("No content to parse")
            return response.headers, []
        return cls._parse(response, output_type, with_headers=True)

    @classmethod
    def parse_atomic(
        cls,
        lexical: str,
        atomic_type: str,
    ) -> str | int | float | Decimal | bool | date | datetime:
        """Convert a lexical value reported with its XML Schema type.

        The REST API reports lexicon values this way, e.g. in /v1/values
        responses. Conversion follows the same rules as typed eval results.

        Parameters
        ----------
        lexical : str
            The value's lexical form.
        atomic_type : str
            Its type name, with or without the ``xs:`` prefix (``xs:decimal``).

        Returns
        -------
        str | int | float | Decimal | bool | date | datetime
            The converted value; types without a conversion stay strings.
        """
        primitive_type = atomic_type.removeprefix("xs:")
        parser = cls._PLAIN_TEXT_PARSERS.get(primitive_type)
        return parser(lexical) if parser else lexical

    @classmethod
    def raise_for_status(
        cls,
        response: Response,
    ) -> None:
        """Raise a MarkLogic error when a response reports failure.

        A success response returns without parsing the body. A non-success
        response is parsed: when MarkLogic described the error a MarkLogicError
        is raised. Empty, malformed and unrecognized error bodies defer to
        httpx, preserving the original response in HTTPStatusError.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance

        Raises
        ------
        MarkLogicError
            If MarkLogic answered a non-success status with an error it described
        HTTPStatusError
            If a non-success status carried no MarkLogic error body
        """
        if response.is_success:
            return
        error = cls._parse_error(response)
        if error:
            logger.debug("MarkLogic error occurred [%s]", error)
            raise MarkLogicError(error)
        response.raise_for_status()

    @classmethod
    def _parse(
        cls,
        response: Response,
        output_type: type | None = None,
        with_headers: bool = False,
    ) -> (
        bytes
        | str
        | int
        | float
        | Decimal
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
        | tuple
    ):
        """Parse a successful MarkLogic HTTP Response.

        Parameters
        ----------
        response : Response
            A success HTTP response taken from MarkLogic instance
        output_type : type | None , default None
            A raw output type (supported: str, bytes)
        with_headers : bool, default False
            Return a (headers, parsed_content) tuple per part when enabled.

        Returns
        -------
        bytes | str | int | float | Decimal | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list | tuple
            A parsed response body. Singletons return their item, and multiple
            items return a list.
        """
        content_type = response.headers.get(const.HEADER_NAME_CONTENT_TYPE, "")
        if content_type.startswith(const.HEADER_MULTIPART_MIXED):
            body_parts = decode_multipart_mixed(response.content, content_type)
        else:
            body_parts = [response]

        parsed_parts = [
            cls._parse_part(body_part, output_type, with_headers)
            for body_part in body_parts
        ]
        if len(parsed_parts) == 1:
            return parsed_parts[0]
        return parsed_parts

    @classmethod
    def _parse_error(
        cls,
        response: Response,
    ) -> dict | str | None:
        """Extract the error MarkLogic described in a non-success response.

        Parameters
        ----------
        response : Response
            A non-success HTTP response

        Returns
        -------
        dict | str | None
            The error object of a JSON or XML error, the error terms of an
            XHTML error page, or None when the body describes no MarkLogic
            error (empty, malformed or produced by a proxy).
        """
        content_type = response.headers.get(const.HEADER_NAME_CONTENT_TYPE, "")
        if content_type.startswith(const.HEADER_JSON):
            return cls._parse_json_error(response)
        if content_type.startswith(const.HEADER_XML):
            return cls._parse_xml_error(response)
        return cls._parse_html_error(response)

    @classmethod
    def _parse_json_error(
        cls,
        response: Response,
    ) -> dict | None:
        """Extract a MarkLogic JSON error response.

        Parameters
        ----------
        response : Response
            A non-success HTTP response with a JSON content type

        Returns
        -------
        dict | None
            The error object, or None when the body is not a MarkLogic error
        """
        try:
            body = response.json()
        except ValueError:
            return None
        return cls._described_error(body)

    @classmethod
    def _parse_xml_error(
        cls,
        response: Response,
    ) -> dict | None:
        """Extract a MarkLogic XML error response as a JSON error object.

        Parameters
        ----------
        response : Response
            A non-success HTTP response with an XML content type

        Returns
        -------
        dict | None
            The error object, or None when the body is not a MarkLogic error
        """
        try:
            xml = ElemTree.fromstring(response.text)
        except ElemTree.ParseError:
            return None
        status_code = xml.findtext("{http://marklogic.com/xdmp/error}status-code")
        return cls._described_error(
            {
                "statusCode": int(status_code)
                if status_code and status_code.isdigit()
                else None,
                "status": xml.findtext("{http://marklogic.com/xdmp/error}status"),
                "messageCode": xml.findtext(
                    "{http://marklogic.com/xdmp/error}message-code",
                ),
                "message": xml.findtext("{http://marklogic.com/xdmp/error}message"),
            },
        )

    @classmethod
    def _parse_html_error(
        cls,
        response: Response,
    ) -> str | None:
        """Extract the error terms of a MarkLogic XHTML error page.

        Parameters
        ----------
        response : Response
            A non-success HTTP response

        Returns
        -------
        str | None
            The error terms joined by new lines, or None when the body is not
            a MarkLogic error page
        """
        try:
            html = ElemTree.fromstring(response.text)
        except ElemTree.ParseError:
            return None
        terms = html.findall(
            "{http://www.w3.org/1999/xhtml}body/"
            "{http://www.w3.org/1999/xhtml}span/"
            "{http://www.w3.org/1999/xhtml}dl/"
            "{http://www.w3.org/1999/xhtml}dt",
        )
        return "\n".join(term.text for term in terms if term.text) or None

    @staticmethod
    def _described_error(
        body: object,
    ) -> dict | None:
        """Return a MarkLogic error object when the body describes one.

        Parameters
        ----------
        body : object
            A decoded error body, with or without the ``errorResponse`` envelope

        Returns
        -------
        dict | None
            The error object when it carries a message code or a message,
            otherwise None
        """
        if not isinstance(body, dict):
            return None
        error = body.get("errorResponse", body)
        if isinstance(error, dict) and any(
            isinstance(error.get(key), str) and error[key]
            for key in ("messageCode", "message")
        ):
            return error
        return None

    @classmethod
    def _parse_part(
        cls,
        body_part: MultipartPart | Response,
        output_type: type | None = None,
        with_headers: bool = False,
    ) -> (
        bytes
        | str
        | int
        | float
        | Decimal
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
        | tuple
    ):
        """Parse one result part without collapsing its content as a sequence.

        Parameters
        ----------
        body_part : MultipartPart | Response
            An HTTP response body or body part taken from MarkLogic instance
        output_type : type | None , default None
            An output type (supported: str, bytes)
        with_headers : bool, default False
            Return a (headers, parsed_content) tuple when enabled.

        Returns
        -------
        bytes | str | int | float | Decimal | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list | tuple
            Parsed content. The input's original content bytes are not changed.

        Raises
        ------
        ValueError
            If a recognized scalar or JSON payload cannot be parsed.
        ParseError
            If XML content is malformed.
        """
        headers = body_part.headers
        if isinstance(body_part, MultipartPart):
            headers = Headers(body_part.headers)
        content_type = headers.get(const.HEADER_NAME_CONTENT_TYPE, "")
        doc_type = Mimetypes.get_doc_type(content_type)

        if (
            output_type is bytes
            or doc_type is DocumentType.BINARY
            or headers.get(const.HEADER_NAME_PRIMITIVE) == const.HEADER_PRIMITIVE_BINARY
        ):
            parsed = body_part.content
            logger.fine("Returning binary response part value")
        elif output_type is str:
            parsed = body_part.text
            logger.fine("Response part parsed to text value: [%s]", parsed)
        else:
            parsed = cls._parse_type_specific(body_part, headers)
            logger.fine("Response part parsed value: [%s]", parsed)

        if not with_headers:
            return parsed
        return headers, parsed

    @classmethod
    def _parse_type_specific(
        cls,
        body_part: MultipartPart | Response,
        headers: Headers,
    ) -> (
        bytes
        | str
        | int
        | float
        | Decimal
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
        | tuple
    ):
        """Parse MarkLogic HTTP Response part to a corresponding python representation.

        Parameters
        ----------
        body_part : MultipartPart | Response
            An HTTP response body or body part taken from MarkLogic instance
        headers : Headers
            HTTP headers

        Returns
        -------
        bytes | str | int | float | Decimal | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list | tuple
            A parsed response body or body part
        """
        content_type = headers.get(const.HEADER_NAME_CONTENT_TYPE, "")
        primitive_type = headers.get(const.HEADER_NAME_PRIMITIVE)
        doc_type = Mimetypes.get_doc_type(content_type)
        if doc_type == DocumentType.TEXT and primitive_type in cls._PLAIN_TEXT_PARSERS:
            return cls.parse_atomic(body_part.text, primitive_type or "")
        if doc_type == DocumentType.JSON:
            return json.loads(body_part.text)
        if doc_type == DocumentType.XML:
            element = ElemTree.fromstring(body_part.text)
            if primitive_type in [None, const.HEADER_PRIMITIVE_DOCUMENT_NODE]:
                return ElemTree.ElementTree(element)
            return element
        return body_part.content


__all__ = ["MLResponseParser"]
