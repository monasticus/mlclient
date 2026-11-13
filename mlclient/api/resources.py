"""ResourcesApi / AsyncResourcesApi - MarkLogic resource service extensions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.resources import (
    ResourceDeleteCall,
    ResourceGetCall,
    ResourcePostCall,
    ResourcePutCall,
)

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class ResourcesApi:
    """Mid-level API for ``/v1/resources/{name}`` endpoints.

    Call resource service extensions (REST extensions) installed in the REST
    API instance.

    Requires a REST app server.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def get(
        self,
        name: str,
        *,
        params: dict | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Make a GET request to a resource service extension.

        Documentation: https://docs.marklogic.com/REST/GET/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourceGetCall(
            name=name,
            params=params,
            database=database,
            txid=txid,
            accept=accept,
        )
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        name: str,
        *,
        params: dict | None = None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Apply an extension-specific POST operation of a resource service extension.

        Documentation: https://docs.marklogic.com/REST/POST/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        body : str | bytes | dict | list | None
            The request body. A dict or list is sent as JSON; a str or bytes
            body requires a content_type.
        content_type : str | None
            The type of the request body. The accepted values are service
            dependent. Defaults to application/json for a dict or list body;
            ``multipart/mixed`` with a boundary sends several documents.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank, or the body is not a dict, list, str or
            bytes, or a str or bytes body has no content_type.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourcePostCall(
            name=name,
            params=params,
            body=body,
            content_type=content_type,
            database=database,
            txid=txid,
            accept=accept,
        )
        return self._api.call(call, timeout=timeout)

    def put(
        self,
        name: str,
        *,
        params: dict | None = None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Perform the PUT operation of a resource service extension.

        Documentation: https://docs.marklogic.com/REST/PUT/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        body : str | bytes | dict | list | None
            The request body. A dict or list is sent as JSON; a str or bytes
            body requires a content_type.
        content_type : str | None
            The type of the request body. The accepted values are service
            dependent. Defaults to application/json for a dict or list body;
            ``multipart/mixed`` with a boundary sends several documents.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank, or the body is not a dict, list, str or
            bytes, or a str or bytes body has no content_type.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourcePutCall(
            name=name,
            params=params,
            body=body,
            content_type=content_type,
            database=database,
            txid=txid,
            accept=accept,
        )
        return self._api.call(call, timeout=timeout)

    def delete(
        self,
        name: str,
        *,
        params: dict | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Send a DELETE request to a resource service extension.

        Documentation: https://docs.marklogic.com/REST/DELETE/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourceDeleteCall(
            name=name,
            params=params,
            database=database,
            txid=txid,
            accept=accept,
        )
        return self._api.call(call, timeout=timeout)


class AsyncResourcesApi:
    """Async mid-level API for ``/v1/resources/{name}`` endpoints.

    Call resource service extensions (REST extensions) installed in the REST
    API instance.

    Requires a REST app server.
    """

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get(
        self,
        name: str,
        *,
        params: dict | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Make a GET request to a resource service extension.

        Documentation: https://docs.marklogic.com/REST/GET/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourceGetCall(
            name=name,
            params=params,
            database=database,
            txid=txid,
            accept=accept,
        )
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        name: str,
        *,
        params: dict | None = None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Apply an extension-specific POST operation of a resource service extension.

        Documentation: https://docs.marklogic.com/REST/POST/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        body : str | bytes | dict | list | None
            The request body. A dict or list is sent as JSON; a str or bytes
            body requires a content_type.
        content_type : str | None
            The type of the request body. The accepted values are service
            dependent. Defaults to application/json for a dict or list body;
            ``multipart/mixed`` with a boundary sends several documents.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank, or the body is not a dict, list, str or
            bytes, or a str or bytes body has no content_type.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourcePostCall(
            name=name,
            params=params,
            body=body,
            content_type=content_type,
            database=database,
            txid=txid,
            accept=accept,
        )
        return await self._api.call(call, timeout=timeout)

    async def put(
        self,
        name: str,
        *,
        params: dict | None = None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Perform the PUT operation of a resource service extension.

        Documentation: https://docs.marklogic.com/REST/PUT/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        body : str | bytes | dict | list | None
            The request body. A dict or list is sent as JSON; a str or bytes
            body requires a content_type.
        content_type : str | None
            The type of the request body. The accepted values are service
            dependent. Defaults to application/json for a dict or list body;
            ``multipart/mixed`` with a boundary sends several documents.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank, or the body is not a dict, list, str or
            bytes, or a str or bytes body has no content_type.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourcePutCall(
            name=name,
            params=params,
            body=body,
            content_type=content_type,
            database=database,
            txid=txid,
            accept=accept,
        )
        return await self._api.call(call, timeout=timeout)

    async def delete(
        self,
        name: str,
        *,
        params: dict | None = None,
        accept: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Send a DELETE request to a resource service extension.

        Documentation: https://docs.marklogic.com/REST/DELETE/v1/resources/[name]

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with the extension's result; several documents
            arrive as ``multipart/mixed``

        Raises
        ------
        WrongParametersError
            If the name is blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ResourceDeleteCall(
            name=name,
            params=params,
            database=database,
            txid=txid,
            accept=accept,
        )
        return await self._api.call(call, timeout=timeout)
