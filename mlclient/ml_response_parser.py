"""The ML Response Parser module.

It exports 1 class:
    * MLResponseParser
        A MarkLogic HTTP response parser.
"""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ElemTree
from datetime import datetime
from typing import ClassVar

from requests import Response
from requests.structures import CaseInsensitiveDict
from requests_toolbelt import MultipartDecoder
from requests_toolbelt.multipart.decoder import BodyPart

from mlclient import constants as const
from mlclient.mimetypes import Mimetypes
from mlclient.structures import DocumentType

logger = logging.getLogger(__name__)


class MLResponseParser:
    """A MarkLogic HTTP response parser.

    MarkLogic returns responses with multipart/mixed content. This class allows to get
    all returned parts as python representations. They are parsed depending on content
    type of corresponding part.

    Examples
    --------
    >>> from mlclient import MLResourcesClient, MLResponseParser
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8002,
    ...     "username": "admin",
    ...     "password": "admin",
    ...     "auth_method": "digest",
    ... }
    >>> with MLResourcesClient(**config) as client:
    ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
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
        const.HEADER_PRIMITIVE_STRING: lambda data: data,
        const.HEADER_PRIMITIVE_INTEGER: lambda data: int(data),
        const.HEADER_PRIMITIVE_DECIMAL: lambda data: float(data),
        const.HEADER_PRIMITIVE_BOOLEAN: lambda data: bool(data),
        const.HEADER_PRIMITIVE_DATE: lambda data: datetime.strptime(
            data,
            "%Y-%m-%d%z",
        ).date(),
        const.HEADER_PRIMITIVE_DATE_TIME: lambda data: datetime.strptime(
            data,
            "%Y-%m-%dT%H:%M:%S.%f%z",
        ),
        None: lambda data: data,
    }

    @classmethod
    def parse(
        cls,
        response: Response,
        output_type: type | None = None,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Parse MarkLogic HTTP Response.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance
        output_type : type | None , default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list
            A parsed response body
        """
        logger.debug("Attempt to parse a response")
        if response.ok and int(response.headers.get("Content-Length")) == 0:
            logger.fine("No content to parse")
            return []

        if output_type == str:
            return cls._parse_text(response)
        if output_type == bytes:
            return cls._parse_bytes(response)

        return cls._parse(response)

    @classmethod
    def parse_with_headers(
        cls,
        response: Response,
        output_type: type | None = None,
    ) -> tuple | list[tuple]:
        """Parse MarkLogic HTTP Response and get headers.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance
        output_type : type | None , default None
            A raw output type (supported: str, bytes)

        Returns
        -------
        tuple
            A parsed response body with headers
        """
        logger.debug("Attempt to parse a response")
        if response.ok and int(response.headers.get("Content-Length")) == 0:
            logger.fine("No content to parse")
            return response.headers, []

        if output_type == str:
            return cls._parse_text(response, with_headers=True)
        if output_type == bytes:
            return cls._parse_bytes(response, with_headers=True)

        return cls._parse(response, with_headers=True)

    @classmethod
    def _parse(
        cls,
        response: Response,
        with_headers: bool = False,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
        | tuple
    ):
        """Parse MarkLogic HTTP Response.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list | tuple
            A parsed response body
        """
        content_type = response.headers.get(const.HEADER_NAME_CONTENT_TYPE)
        if not response.ok:
            if content_type.startswith(const.HEADER_JSON):
                error = response.json()
            elif content_type.startswith(const.HEADER_XML):
                error = cls._parse_xml_error(response)
            else:
                error = cls._parse_html_error(response)
            logger.warning("MarkLogic error occurred [%s]", error)
            if with_headers:
                return response.headers, error
            return error

        if content_type.startswith(const.HEADER_MULTIPART_MIXED):
            body_parts = MultipartDecoder.from_response(response).parts
        else:
            body_parts = [response]

        parsed_parts = [
            cls._parse_part(body_part, None, with_headers) for body_part in body_parts
        ]
        if len(parsed_parts) == 1:
            return parsed_parts[0]
        return parsed_parts

    @classmethod
    def _parse_text(
        cls,
        response: Response,
        with_headers: bool = False,
    ) -> str | tuple | list:
        """Parse MarkLogic HTTP Response to string.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance

        Returns
        -------
        str | tuple | list
            A parsed response body in string format
        """
        content_type = response.headers.get(const.HEADER_NAME_CONTENT_TYPE)
        if not response.ok:
            if content_type.startswith(const.HEADER_JSON):
                json_error = response.json()
                error = json.dumps(json_error)
            elif content_type.startswith(const.HEADER_XML):
                json_error = cls._parse_xml_error(response)
                error = json.dumps(json_error)
            else:
                error = cls._parse_html_error(response)
            logger.warning("MarkLogic error occurred [%s]", error)
            if with_headers:
                return response.headers, error
            return error

        if content_type.startswith(const.HEADER_MULTIPART_MIXED):
            body_parts = MultipartDecoder.from_response(response).parts
        else:
            body_parts = [response]

        parsed_parts = [
            cls._parse_part(body_part, str, with_headers) for body_part in body_parts
        ]
        if len(parsed_parts) == 1:
            return parsed_parts[0]
        return parsed_parts

    @classmethod
    def _parse_bytes(
        cls,
        response: Response,
        with_headers: bool = False,
    ) -> bytes | tuple | list:
        """Parse MarkLogic HTTP Response to bytes.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance

        Returns
        -------
        bytes | tuple | list
            A parsed response body in bytes format
        """
        content_type = response.headers.get(const.HEADER_NAME_CONTENT_TYPE)
        if not response.ok:
            if content_type.startswith(const.HEADER_JSON):
                json_error = response.json()
                error = json.dumps(json_error).encode("utf-8")
            elif content_type.startswith(const.HEADER_XML):
                json_error = cls._parse_xml_error(response)
                error = json.dumps(json_error).encode("utf-8")
            else:
                error = cls._parse_html_error(response).encode("utf-8")
            logger.warning("MarkLogic error occurred [%s]", error)
            if with_headers:
                return response.headers, error
            return error

        if content_type.startswith(const.HEADER_MULTIPART_MIXED):
            body_parts = MultipartDecoder.from_response(response).parts
        else:
            body_parts = [response]

        parsed_parts = [
            cls._parse_part(body_part, bytes, with_headers) for body_part in body_parts
        ]
        if len(parsed_parts) == 1:
            return parsed_parts[0]
        return parsed_parts

    @classmethod
    def _parse_xml_error(
        cls,
        response: Response,
    ) -> dict:
        """Parse MarkLogic XML error response to JSON.

        Parameters
        ----------
        response : Response
            A non-OK HTTP response taken from MarkLogic instance

        Returns
        -------
        dict
            A parsed JSON error
        """
        xml = ElemTree.fromstring(response.text)
        status_code = xml.find("{http://marklogic.com/xdmp/error}status-code")
        status = xml.find("{http://marklogic.com/xdmp/error}status")
        msg_code = xml.find("{http://marklogic.com/xdmp/error}message-code")
        msg = xml.find("{http://marklogic.com/xdmp/error}message")
        return {
            "errorResponse": {
                "statusCode": int(status_code.text),
                "status": status.text,
                "messageCode": msg_code.text,
                "message": msg.text,
            },
        }

    @classmethod
    def _parse_html_error(
        cls,
        response: Response,
    ) -> str:
        """Parse MarkLogic HTML error response.

        Parameters
        ----------
        response : Response
            A non-OK HTTP response taken from MarkLogic instance

        Returns
        -------
        str
            A parsed error description
        """
        html = ElemTree.fromstring(response.text)
        terms = html.findall(
            "{http://www.w3.org/1999/xhtml}body/"
            "{http://www.w3.org/1999/xhtml}span/"
            "{http://www.w3.org/1999/xhtml}dl/"
            "{http://www.w3.org/1999/xhtml}dt",
        )
        return "\n".join(term.text for term in terms)

    @classmethod
    def _parse_part(
        cls,
        body_part: BodyPart | Response,
        output_type: type | None = None,
        with_headers: bool = False,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
        | tuple
    ):
        """Parse MarkLogic HTTP Response part.

        Parameters
        ----------
        body_part : BodyPart | Response
            An HTTP response body or body part taken from MarkLogic instance
        output_type : type | None , default None
            An output type (supported: str, bytes)

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list | tuple
            A parsed response body or body part
        """
        headers = body_part.headers
        if isinstance(body_part, BodyPart):
            headers = cls._decode_headers(headers, body_part.encoding)
        content_type = headers.get(const.HEADER_NAME_CONTENT_TYPE)
        doc_type = Mimetypes.get_doc_type(content_type)

        if output_type is bytes or doc_type is DocumentType.BINARY:
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
        body_part: BodyPart | Response,
        headers: CaseInsensitiveDict,
    ) -> (
        bytes
        | str
        | int
        | float
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
        body_part : BodyPart | Response
            An HTTP response body or body part taken from MarkLogic instance
        headers : CaseInsensitiveDict
            HTTP headers

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list | tuple
            A parsed response body or body part
        """
        content_type = headers.get(const.HEADER_NAME_CONTENT_TYPE)
        primitive_type = headers.get(const.HEADER_NAME_PRIMITIVE)
        doc_type = Mimetypes.get_doc_type(content_type)
        if doc_type == DocumentType.TEXT and primitive_type in cls._PLAIN_TEXT_PARSERS:
            return cls._PLAIN_TEXT_PARSERS[primitive_type](body_part.text)
        if doc_type == DocumentType.JSON:
            return json.loads(body_part.text)
        if doc_type == DocumentType.XML:
            element = ElemTree.fromstring(body_part.text)
            if primitive_type in [None, const.HEADER_PRIMITIVE_DOCUMENT_NODE]:
                return ElemTree.ElementTree(element)
            return element
        return body_part.content

    @staticmethod
    def _decode_headers(
        headers: dict,
        encoding: str,
    ) -> CaseInsensitiveDict:
        """Decode HTTP headers from bytes format.

        Parameters
        ----------
        headers : dict
            Encoded HTTP headers
        encoding : str
            An encoding type

        Returns
        -------
        CaseInsensitiveDict
            Decoded HTTP headers
        """
        headers_dict = {
            name.decode(encoding): value.decode(encoding)
            for name, value in headers.items()
        }
        return CaseInsensitiveDict(**headers_dict)
