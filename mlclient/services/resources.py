"""Higher-level resource extensions service (ResourcesService / AsyncResourcesService).

Calls resource service extensions (REST extensions) and parses their results.
"""

from __future__ import annotations

from mlclient import _constants as constants
from mlclient import exceptions
from mlclient._options import UNSET
from mlclient.models.documents import Document, MetadataDocument
from mlclient.models.mimetypes import Mimetypes
from mlclient.models.results import ParsedValue
from mlclient.models.types import DocumentType
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.services._execution import ExecutionService

ResourceBody = dict | list | str | bytes | Document | list[Document] | None
"""A request body of a resource extension call."""

_DOCUMENT_TYPE_CONTENT_TYPES = {
    DocumentType.JSON: constants.HEADER_JSON,
    DocumentType.XML: constants.HEADER_XML,
    DocumentType.TEXT: constants.HEADER_PLAIN_TEXT,
    DocumentType.BINARY: "application/octet-stream",
}


class ResourcesService(ExecutionService):
    """Higher-level service for /v1/resources/{name} endpoints.

    Calls resource service extensions installed in the REST API instance of
    the connection and parses their results like ``ml.eval``. Calling requires
    the rest-reader privilege, and rest-writer for POST, PUT and DELETE.
    """

    def get(
        self,
        name: str,
        params: dict | None = None,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the GET method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        response = self._rest.resources.get(
            name,
            params=params,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)

    def post(
        self,
        name: str,
        body: ResourceBody = None,
        params: dict | None = None,
        *,
        content_type: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the POST method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        body : dict | list | str | bytes | Document | list[Document] | None
            The extension's input. A dict or list is sent as JSON; str or bytes
            need a content_type; a Document is sent with the content type of
            its URI extension or document type; a list of Documents is sent as
            ``multipart/mixed``, one part each. Without a body the extension
            still runs.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        content_type : str | None, default None
            The type of a str or bytes body, or a replacement for
            application/json for a dict or list body. Documents carry their own.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank, the body type is not supported, a str or
            bytes body has no content_type, or a content_type accompanies
            Documents.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        body, content_type = _encode_body(body, content_type)
        response = self._rest.resources.post(
            name,
            params=params,
            body=body,
            content_type=content_type,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)

    def put(
        self,
        name: str,
        body: ResourceBody = None,
        params: dict | None = None,
        *,
        content_type: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the PUT method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        body : dict | list | str | bytes | Document | list[Document] | None
            The extension's input. A dict or list is sent as JSON; str or bytes
            need a content_type; a Document is sent with the content type of
            its URI extension or document type; a list of Documents is sent as
            ``multipart/mixed``, one part each.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        content_type : str | None, default None
            The type of a str or bytes body, or a replacement for
            application/json for a dict or list body. Documents carry their own.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank, the body type is not supported, a str or
            bytes body has no content_type, or a content_type accompanies
            Documents.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        body, content_type = _encode_body(body, content_type)
        response = self._rest.resources.put(
            name,
            params=params,
            body=body,
            content_type=content_type,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)

    def delete(
        self,
        name: str,
        params: dict | None = None,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the DELETE method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        response = self._rest.resources.delete(
            name,
            params=params,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)


class AsyncResourcesService(ExecutionService):
    """Async higher-level service for /v1/resources/{name} endpoints.

    Calls resource service extensions installed in the REST API instance of
    the connection and parses their results like ``ml.eval``. Calling requires
    the rest-reader privilege, and rest-writer for POST, PUT and DELETE.
    """

    async def get(
        self,
        name: str,
        params: dict | None = None,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the GET method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        response = await self._rest.resources.get(
            name,
            params=params,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)

    async def post(
        self,
        name: str,
        body: ResourceBody = None,
        params: dict | None = None,
        *,
        content_type: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the POST method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        body : dict | list | str | bytes | Document | list[Document] | None
            The extension's input. A dict or list is sent as JSON; str or bytes
            need a content_type; a Document is sent with the content type of
            its URI extension or document type; a list of Documents is sent as
            ``multipart/mixed``, one part each. Without a body the extension
            still runs.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        content_type : str | None, default None
            The type of a str or bytes body, or a replacement for
            application/json for a dict or list body. Documents carry their own.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank, the body type is not supported, a str or
            bytes body has no content_type, or a content_type accompanies
            Documents.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        body, content_type = _encode_body(body, content_type)
        response = await self._rest.resources.post(
            name,
            params=params,
            body=body,
            content_type=content_type,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)

    async def put(
        self,
        name: str,
        body: ResourceBody = None,
        params: dict | None = None,
        *,
        content_type: str | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the PUT method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        body : dict | list | str | bytes | Document | list[Document] | None
            The extension's input. A dict or list is sent as JSON; str or bytes
            need a content_type; a Document is sent with the content type of
            its URI extension or document type; a list of Documents is sent as
            ``multipart/mixed``, one part each.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        content_type : str | None, default None
            The type of a str or bytes body, or a replacement for
            application/json for a dict or list body. Documents carry their own.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank, the body type is not supported, a str or
            bytes body has no content_type, or a content_type accompanies
            Documents.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        body, content_type = _encode_body(body, content_type)
        response = await self._rest.resources.put(
            name,
            params=params,
            body=body,
            content_type=content_type,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)

    async def delete(
        self,
        name: str,
        params: dict | None = None,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        timeout=UNSET,
    ) -> ParsedValue:
        """Call the DELETE method of a resource extension and parse its result.

        Parameters
        ----------
        name : str
            The name of the installed resource extension.
        params : dict | None, default None
            Extension parameters by name without the ``rs:`` prefix; a name
            that already has it is sent unchanged. A list value is repeated,
            so the extension receives a sequence. Booleans are sent as
            ``true`` / ``false``, other values as strings; None is omitted.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue
            JSON as dict or list, XML as an element tree, text as str. Several
            documents return a list, no content returns [].

        Raises
        ------
        WrongParametersError
            If the name is blank.
        MarkLogicError
            If MarkLogic returns an error, including an extension that is not
            installed or does not implement the method.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        response = await self._rest.resources.delete(
            name,
            params=params,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, None)


def _encode_body(
    body: ResourceBody,
    content_type: str | None,
) -> tuple[dict | list | str | bytes | None, str | None]:
    """Encode Documents as a request body; leave other bodies to the endpoint.

    Parameters
    ----------
    body : dict | list | str | bytes | Document | list[Document] | None
        A resource extension call's input.
    content_type : str | None
        The explicit content type of the body.

    Returns
    -------
    tuple[dict | list | str | bytes | None, str | None]
        A Document becomes its content bytes and content type; a nonempty list
        of Documents a ``multipart/mixed`` body with its boundary. Other bodies
        and the content type are returned unchanged.

    Raises
    ------
    WrongParametersError
        If a content type accompanies Documents, or a Document has no content.
    """
    documents = _documents(body)
    if documents is None:
        return body, content_type
    if content_type is not None:
        msg = "A Document body carries its own content type; omit content_type!"
        raise exceptions.WrongParametersError(msg)
    if isinstance(body, Document):
        return body.content_bytes, _document_content_type(body)
    return encode_multipart_mixed([_document_part(document) for document in documents])


def _documents(body: ResourceBody) -> list[Document] | None:
    """Return the Documents of a body, or None when it holds no Document.

    Parameters
    ----------
    body : dict | list | str | bytes | Document | list[Document] | None
        A resource extension call's input.

    Returns
    -------
    list[Document] | None
        The Document as a one-item list, the Documents of a nonempty list of
        Documents, or None.

    Raises
    ------
    WrongParametersError
        If a Document has no content.
    """
    if isinstance(body, Document):
        documents = [body]
    elif (
        isinstance(body, list)
        and body
        and all(isinstance(item, Document) for item in body)
    ):
        documents = body
    else:
        return None
    if any(type(document) is MetadataDocument for document in documents):
        msg = "A MetadataDocument has no content to send to a resource extension!"
        raise exceptions.WrongParametersError(msg)
    return documents


def _document_part(document: Document) -> MultipartPart:
    """Return a Document as one part of a multipart/mixed body.

    Parameters
    ----------
    document : Document
        A document with content.

    Returns
    -------
    MultipartPart
        The document content with its Content-Type header.
    """
    return MultipartPart(
        headers={constants.HEADER_NAME_CONTENT_TYPE: _document_content_type(document)},
        content=document.content_bytes,
    )


def _document_content_type(document: Document) -> str:
    """Return the content type of a Document.

    Parameters
    ----------
    document : Document
        A document with content.

    Returns
    -------
    str
        The mimetype of the URI extension, or the document type's default when
        the URI is missing or its extension unknown.
    """
    mimetype = Mimetypes.get_mimetype(document.uri) if document.uri else None
    return mimetype or _DOCUMENT_TYPE_CONTENT_TYPES[document.doc_type]
