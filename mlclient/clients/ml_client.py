"""The ML Client module.

It exports 3 classes:
    * MLClient
        A low-level class used to send simple HTTP requests to a MarkLogic instance.
    * MLResourceClient
        An MLClient subclass calling ResourceCall implementation classes.
    * MLResourcesClient
        An MLResourceClient subclass supporting REST Resources of the MarkLogic server.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from types import TracebackType
import ssl

import httpx
from httpx import Auth, BasicAuth, Client, DigestAuth, Response, HTTPTransport
from httpx_retries import Retry, RetryTransport

from mlclient import constants as const
from mlclient.calls import (
    DatabaseDeleteCall,
    DatabaseGetCall,
    DatabasePostCall,
    DatabasePropertiesGetCall,
    DatabasePropertiesPutCall,
    DatabasesGetCall,
    DatabasesPostCall,
    DocumentsDeleteCall,
    DocumentsGetCall,
    DocumentsPostCall,
    EvalCall,
    ForestDeleteCall,
    ForestGetCall,
    ForestPostCall,
    ForestPropertiesGetCall,
    ForestPropertiesPutCall,
    ForestsGetCall,
    ForestsPostCall,
    ForestsPutCall,
    LogsCall,
    ResourceCall,
    RoleDeleteCall,
    RoleGetCall,
    RolePropertiesGetCall,
    RolePropertiesPutCall,
    RolesGetCall,
    RolesPostCall,
    ServerDeleteCall,
    ServerGetCall,
    ServerPropertiesGetCall,
    ServerPropertiesPutCall,
    ServersGetCall,
    ServersPostCall,
    UserDeleteCall,
    UserGetCall,
    UserPropertiesGetCall,
    UserPropertiesPutCall,
    UsersGetCall,
    UsersPostCall,
)
from mlclient.mimetypes import Mimetypes
from mlclient.structures import DocumentType
from mlclient.structures.calls import DocumentsBodyPart
from .restart_waiter import RestartWaiter

logger = logging.getLogger(__name__)

MARKLOGIC_REST_API_PORT = 8000
MARKLOGIC_ADMIN_API_PORT = 8001
MARKLOGIC_MANAGE_API_PORT = 8002
# Reuse a single SSL context across all clients. Without this, every
# HTTPTransport() call invokes ssl.SSLContext.load_verify_locations which
# re-reads the system CA bundle from disk (~60-120 ms each).
_SHARED_SSL_CONTEXT = ssl.create_default_context()
DEFAULT_RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=0.5,
)
RESTART_RETRY_STRATEGY = Retry(
    total=12,
    allowed_methods=["GET"],
    status_forcelist=[
        httpx.codes.BAD_GATEWAY,
        httpx.codes.SERVICE_UNAVAILABLE,
        httpx.codes.GATEWAY_TIMEOUT,
    ],
    retry_on_exceptions=[
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.RemoteProtocolError,
    ],
    backoff_factor=1.0,
)


class MLClient:
    """A low-level class used to send simple HTTP requests to a MarkLogic instance.

    Using configuration details provided it allows you to hit MarkLogic's endpoints.
    It can connect with the MarkLogic Server as a Context Manager or explicitly by
    using the connect method.

    Attributes
    ----------
    protocol : str
        a protocol used for HTTP requests (http / https)
    host : str
        a host name
    port : int
        an App Service port
    auth_method : str
        an authorization method (basic / digest)
    username : str
        a username
    password : str
        a password
    base_url : str
        a base url built based on the protocol, the host name and the port provided

    Examples
    --------
    >>> from mlclient import MLClient
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8002,
    ...     "username": "admin",
    ...     "password": "admin",
    ... }
    >>> with MLClient(**config) as client:
    ...     resp = client.post(
    ...         endpoint="/v1/eval",
    ...         body={"xquery": "xdmp:database() => xdmp:database-name()"})
    ...     print(resp.text)
    ...
    --6a5df7d535c71968
    Content-Type: text/plain
    X-Primitive: string
    App-Services
    --6a5df7d535c71968--
    """

    def __init__(
        self,
        protocol: str = "http",
        host: str = "localhost",
        port: int = MARKLOGIC_MANAGE_API_PORT,
        auth_method: str = "basic",
        username: str = "admin",
        password: str = "admin",
        retry: Retry | None = None,
    ):
        """Initialize MLClient instance.

        Parameters
        ----------
        protocol : str, default "http"
            A protocol used for HTTP requests (http / https)
        host : str, default "localhost"
            A host name
        port : int, default 8002
            An App Service port
        auth_method : str, default "basic"
            An authorization method (basic / digest)
        username : str, default "admin"
            A username
        password : str, default "admin"
            A password
        retry : Retry, default Retry(total=5,backoff_factor=0.5)
            A retry strategy
        """
        self.protocol: str = protocol
        self.host: str = host
        self.port: int = port
        self.auth_method: str = auth_method
        self.username: str = username
        self.password: str = password
        self.base_url: str = f"{protocol}://{host}:{port}"
        self._retry: Retry = retry or DEFAULT_RETRY_STRATEGY
        self._client: Client | None = None
        auth_impl = BasicAuth if auth_method == "basic" else DigestAuth
        self._auth: Auth = auth_impl(username, password)

    def __enter__(
        self,
    ):
        """Enter the MLClient instance.

        It starts an HTTP session.

        Returns
        -------
        self : MLClient
            A MLClient instance
        """
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type,
        exc_val: BaseException,
        exc_tb: TracebackType,
    ):
        """Exit the MLClient instance.

        It closes an HTTP session.

        Parameters
        ----------
        exc_type : type | None
            An exception's type
        exc_val : BaseException | None
            An exception's value
        exc_tb  TracebackType | None
            An exception's traceback
        """
        self.disconnect()

    def connect(
        self,
    ):
        """Start an HTTP session."""
        logger.debug("Initiating a connection with %s", self.base_url)
        transport = HTTPTransport(verify=_SHARED_SSL_CONTEXT)
        self._client = Client(transport=RetryTransport(transport=transport, retry=self._retry))

    def disconnect(
        self,
    ):
        """Close an HTTP session."""
        if self._client:
            logger.debug("Closing a connection")
            self._client.close()
            self._client = None

    def is_connected(
        self,
    ) -> bool:
        """Return a connection status.

        Returns
        -------
        bool
            True if the client has started a connection; otherwise False
        """
        return self._client is not None

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send a GET request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict
            Request parameters
        headers : dict
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("GET", endpoint, params, headers)

    def post(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
        body: str | dict | None = None,
    ) -> Response:
        """Send a POST request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict
            Request parameters
        headers : dict
            Request headers
        body : str | dict
            A request body

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("POST", endpoint, params, headers, body)

    def put(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
        body: str | dict | None = None,
    ) -> Response:
        """Send a PUT request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict
            Request parameters
        headers : dict
            Request headers
        body : str | dict
            A request body

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("PUT", endpoint, params, headers, body)

    def delete(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send a DELETE request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict
            Request parameters
        headers : dict
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("DELETE", endpoint, params, headers)

    def request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None,
        body: str | dict | None = None,
    ) -> Response:
        """Send an HTTP request.

        Parameters
        ----------
        method : str
            An HTTP request method
        endpoint : str
            A REST endpoint to call
        params : dict
            Request parameters
        headers : dict
            Request headers
        body : str | dict
            A request body

        Returns
        -------
        Response
            An HTTP response
        """
        request = self._prepare_request(params, headers, body)
        resp = self._send_request(method, endpoint, request)
        self._log_response(method, endpoint, resp)
        return resp

    def wait_for_restart_completion(
        self,
        response: Response | None = None,
        timeout: float = 30.0,
        poll_interval: float = 0.25,
        retry: Retry | None = None,
    ) -> None:
        """Wait for MarkLogic readiness after a restart-signaling response.

        Use this after operations that may return MarkLogic restart metadata.
        If ``response`` is a recognized restart response, the method waits until
        all affected hosts report readiness through ``/admin/v1/timestamp``.
        Otherwise, it performs a single readiness probe for the current host.

        Parameters
        ----------
        response : Response | None
            Optional response returned by an operation that may have initiated a
            restart.
        timeout : float
            Maximum number of seconds to wait for readiness.
        poll_interval : float
            Delay between readiness probes while waiting for a host to recover.
        retry : Retry | None
            Retry strategy used for readiness probes. If omitted, restart-aware
            retry settings are used.

        Raises
        ------
        ValueError
            If a multi-host restart response cannot be resolved to MarkLogic
            host names.
        TimeoutError
            If MarkLogic does not report readiness before ``timeout`` expires.
        AssertionError
            If the readiness probe returns a non-retryable non-``200`` status.
        RuntimeError
            If called from a running event loop.
        """
        admin_retry = retry or RESTART_RETRY_STRATEGY
        self._get_restart_waiter().wait_for_restart_completion(
            response,
            timeout,
            poll_interval,
            admin_retry,
        )

    def _get_restart_waiter(self) -> RestartWaiter:
        """Return a helper handling restart payload parsing and readiness waits."""
        return RestartWaiter(
            protocol=self.protocol,
            host=self.host,
            auth=self._auth,
            default_retry=self._retry,
        )

    def _prepare_request(
        self,
        params: dict | None = None,
        headers: dict | None = None,
        body: str | dict | None = None,
    ) -> dict:
        """Prepare a request details."""
        request = {
            "params": params or {},
            "headers": headers or {},
            "auth": self._auth,
        }
        if body is not None:
            content_type = headers.get(const.HEADER_NAME_CONTENT_TYPE)
            doc_type = Mimetypes.get_doc_type(content_type) if content_type else None
            if doc_type == DocumentType.JSON:
                request["json"] = body
            elif isinstance(body, Mapping):
                request["data"] = body
            else:
                request["content"] = body

        logger.fine(
            "Request details: %s",
            " ".join(
                f"{k} [{v if k != 'auth' else v.__class__.__name__}]"
                for k, v in request.items()
            ),
        )
        return request

    def _send_request(
        self,
        method: str,
        endpoint: str,
        request: dict,
    ) -> Response:
        """Send a request."""
        logger.info("Sending a request... %s %s", method.upper(), endpoint)

        url = self.base_url + endpoint
        if self.is_connected():
            resp = self._client.request(method, url, **request)
        else:
            logger.warning(
                "MLClient is not connected -- "
                "A request will be sent in an ad-hoc initialized session (%s %s)",
                method.upper(),
                endpoint,
            )
            with Client(transport=RetryTransport(retry=self._retry)) as client:
                resp = client.request(method, url, **request)

        return resp

    def _log_response(
        self,
        method: str,
        endpoint: str,
        response: Response,
    ):
        """Log response details and restart warning, if applicable."""
        logger.debug("Response retrieved")
        if logger.isEnabledFor(logging.FINE):
            logger.fine(
                "Response:\n%s",
                self._format_http_response(response),
            )

        if RestartWaiter.is_restart_response(response):
            logger.warning(
                "MarkLogic accepted %s %s and initiated a restart; "
                "Location [%s]. Wait for restart completion before "
                "sending follow-up requests",
                method,
                endpoint,
                response.headers.get("Location"),
            )

    @staticmethod
    def _format_http_response(
        response: Response,
    ) -> str:
        """Format an HTTP response in a protocol-like representation."""
        reason_phrase = httpx.codes.get_reason_phrase(response.status_code)
        start_line = f"HTTP/1.1 {response.status_code} {reason_phrase}"
        headers = "\n".join(
            f"{name}: {val}"
            for name, val in response.headers.items()
        )
        if response.text:
            return f"{start_line}\n{headers}\n\n{response.text}"
        return f"{start_line}\n{headers}"


class MLResourceClient(MLClient):
    """An MLClient subclass calling ResourceCall implementation classes.

    It can connect with the MarkLogic Server as a Context Manager or explicitly by
    using the connect method.

    You can call ML REST Resource by using the call() method accepting a ResourceCall
    implementation classes.

    Attributes
    ----------
    All attributes are inherited from the MLClient superclass.

    Examples
    --------
    >>> from mlclient import MLResourceClient
    >>> from mlclient.calls import EvalCall
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8002,
    ...     "username": "admin",
    ...     "password": "admin",
    ... }
    >>> with MLResourceClient(**config) as client:
    ...     eval_call = EvalCall(xquery="xdmp:database() => xdmp:database-name()")
    ...     resp = client.call(eval_call)
    ...     print(resp.text)
    ...
    --6a5df7d535c71968
    Content-Type: text/plain
    X-Primitive: string
    App-Services
    --6a5df7d535c71968--
    """

    def call(
        self,
        call: ResourceCall,
    ) -> Response:
        """Send a custom request to a MarkLogic endpoint.

        Parameters
        ----------
        call : ResourceCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request(
            method=call.method,
            endpoint=call.endpoint,
            params=call.params,
            headers=call.headers,
            body=call.body,
        )


class MLResourcesClient(MLResourceClient):
    """An MLResourceClient subclass supporting REST Resources of the MarkLogic server.

    It can connect with the MarkLogic Server as a Context Manager or explicitly by
    using the connect method.

    There are two ways to call ML REST Resources:
    - by using defined methods corresponding to a resource (e.g. /v1/eval -> eval())
    - by using the call() method accepting a ResourceCall implementation classes.

    This class can be treated as an example of MLClient class extension for your own
    dedicated APIs or as a superclass for your client.

    Attributes
    ----------
    All attributes are inherited from the MLClient superclass.

    Examples
    --------
    >>> from mlclient import MLResourcesClient
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8002,
    ...     "username": "admin",
    ...     "password": "admin",
    ... }
    >>> with MLResourcesClient(**config) as client:
    ...     resp = client.eval(xquery="xdmp:database() => xdmp:database-name()")
    ...     print(resp.text)
    ...
    --6a5df7d535c71968
    Content-Type: text/plain
    X-Primitive: string
    App-Services
    --6a5df7d535c71968--
    """

    def eval(
        self,
        xquery: str | None = None,
        javascript: str | None = None,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
    ) -> Response:
        """Send a POST request to the /v1/eval endpoint.

        Parameters
        ----------
        xquery : str
            The query to evaluate, expressed using XQuery.
            You must include either this parameter or the javascript parameter,
            but not both.
        javascript : str
            The query to evaluate, expressed using server-side JavaScript.
            You must include either this parameter or the xquery parameter,
            but not both.
        variables
            External variables to pass to the query during evaluation
        database
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid
            The transaction identifier of the multi-statement transaction
            in which to service this request.

        Returns
        -------
        Response
            An HTTP response
        """
        call = EvalCall(
            xquery=xquery,
            javascript=javascript,
            variables=variables,
            database=database,
            txid=txid,
        )
        return self.call(call)

    def get_logs(
        self,
        filename: str,
        data_format: str | None = None,
        host: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        regex: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/logs endpoint.

        Parameters
        ----------
        filename : str
            The log file to be returned.
        data_format : str
            The format of the data in the log file. The supported formats are xml, json
            or html.
        host : str
            The host from which to return the log data.
        start_time : str
            The start time for the log data.
        end_time : str
            The end time for the log data.
        regex : str
            Filters the log data, based on a regular expression.

        Returns
        -------
        Response
            An HTTP response
        """
        call = LogsCall(
            filename=filename,
            data_format=data_format,
            host=host,
            start_time=start_time,
            end_time=end_time,
            regex=regex,
        )
        return self.call(call)

    def get_databases(
        self,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases endpoint.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be schema, properties-schema, metrics, package, describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasesGetCall(data_format=data_format, view=view)
        return self.call(call)

    def post_databases(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/databases endpoint.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasesPostCall(body=body)
        return self.call(call)

    def get_database(
        self,
        database: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases/{id|name} endpoint.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data.
            Can be properties-schema, package, describe, config, counts, edit, status,
            forest-storage, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabaseGetCall(database=database, data_format=data_format, view=view)
        return self.call(call)

    def post_database(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/databases/{id|name} endpoint.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePostCall(database=database, body=body)
        return self.call(call)

    def delete_database(
        self,
        database: str,
        forest_delete: str | None = None,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/databases/{id|name} endpoint.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        forest_delete : str
            Specifies to delete the forests attached to the database.
            If unspecified, the forests will not be affected.
            If "configuration" is specified, the forest configuration will be removed
            but public forest data will remain.
            If "data" is specified, the forest configuration and data will be removed.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabaseDeleteCall(database=database, forest_delete=forest_delete)
        return self.call(call)

    def get_database_properties(
        self,
        database: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/databases/{id|name}/properties endpoint.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePropertiesGetCall(database=database, data_format=data_format)
        return self.call(call)

    def put_database_properties(
        self,
        database: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/databases/{id|name}/properties endpoint.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = DatabasePropertiesPutCall(database=database, body=body)
        return self.call(call)

    def get_servers(
        self,
        data_format: str | None = None,
        group_id: str | None = None,
        view: str | None = None,
        full_refs: bool | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/servers endpoint.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        group_id : str
            Specifies to return only the servers in the specified group.
            The group can be identified either by id or name.
            If not specified, the response includes information about all App Servers.
        view : str
            A specific view of the returned data.
            Can be schema, properties-schema, metrics, package, describe, or default.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references. This parameter is not meaningful with view=package.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ServersGetCall(
            data_format=data_format,
            group_id=group_id,
            view=view,
            full_refs=full_refs,
        )
        return self.call(call)

    def post_servers(
        self,
        body: str | dict,
        group_id: str | None = None,
        server_type: str | None = None,
    ) -> Response:
        """Send a POST request to the /manage/v2/servers endpoint.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.
        group_id : str
            The id or name of the group to which the App Server belongs.
            The group must be specified by this parameter or by the group-name property
            in the request payload. If it is specified in both places, the values
            must be the same.
        server_type : str
            The type of App Server to create.
            The App Server type must be specified by this parameter or in the request
            payload. If it is specified in both places, the values must be the same.
            The valid types are: http, odbc, xdbc, or webdav.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ServersPostCall(body=body, group_id=group_id, server_type=server_type)
        return self.call(call)

    def get_server(
        self,
        server: str,
        group_id: str,
        data_format: str | None = None,
        view: str | None = None,
        host_id: str | None = None,
        full_refs: bool | None = None,
        modules: bool | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/servers/{id|name} endpoint.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be properties-schema, config, edit, package, describe, status,
            xdmp:server-status or default.
        host_id : str
            Meaningful only when view=status. Specifies to return the status
            for the server in the specified host. The host can be identified
            either by id or name.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references. This parameter is not meaningful with view=package.
        modules : bool
            Meaningful only with view=package. Whether to include a manifest
            of the modules database for the App Server in the results, if one exists.
            It is an error to request a modules database manifest for an App Server
            that uses the filesystem for modules. Default: false.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ServerGetCall(
            server=server,
            group_id=group_id,
            data_format=data_format,
            view=view,
            host_id=host_id,
            full_refs=full_refs,
            modules=modules,
        )
        return self.call(call)

    def delete_server(
        self,
        server: str,
        group_id: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/servers/{id|name} endpoint.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ServerDeleteCall(server=server, group_id=group_id)
        return self.call(call)

    def get_server_properties(
        self,
        server: str,
        group_id: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/servers/{id|name}/properties endpoint.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ServerPropertiesGetCall(
            server=server,
            group_id=group_id,
            data_format=data_format,
        )
        return self.call(call)

    def put_server_properties(
        self,
        server: str,
        group_id: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/servers/{id|name}/properties endpoint.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ServerPropertiesPutCall(server=server, group_id=group_id, body=body)
        return self.call(call)

    def get_forests(
        self,
        data_format: str | None = None,
        view: str | None = None,
        database: str | None = None,
        group: str | None = None,
        host: str | None = None,
        full_refs: bool | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/forests endpoint.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be either describe, default, status, metrics, schema, storage,
            or properties-schema.
        database : str
            Returns a summary of the forests for the specified database.
            The database can be identified either by id or name.
        group : str
            Returns a summary of the forests for the specified group.
            The group can be identified either by id or name.
        host : str
            Returns a summary of the forests for the specified host.
            The host can be identified either by id or name.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestsGetCall(
            data_format=data_format,
            view=view,
            database=database,
            group=group,
            host=host,
            full_refs=full_refs,
        )
        return self.call(call)

    def post_forests(
        self,
        body: str | dict,
        wait_for_forest_to_mount: bool | None = None,
    ) -> Response:
        """Send a POST request to the /manage/v2/forests endpoint.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.
        wait_for_forest_to_mount : bool
            Whether to wait for the new forest to mount before sending a response
            to this request. Allowed values: true (default) or false.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestsPostCall(
            body=body,
            wait_for_forest_to_mount=wait_for_forest_to_mount,
        )
        return self.call(call)

    def put_forests(
        self,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/forests endpoint.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestsPutCall(body=body)
        return self.call(call)

    def get_forest(
        self,
        forest: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/forests/{id|name} endpoint.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be properties-schema, config, edit, package, describe, status,
            xdmp:server-status or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestGetCall(forest=forest, data_format=data_format, view=view)
        return self.call(call)

    def post_forest(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/forests/{id|name} endpoint.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : dict
            A list of properties. Need to include the 'state' property
            (the type of state change to initiate).
            Allowed values: clear, merge, restart, attach, detach, retire, employ.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestPostCall(forest=forest, body=body)
        return self.call(call)

    def delete_forest(
        self,
        forest: str,
        level: str,
        replicas: str | None = None,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/forests/{id|name} endpoint.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        level : str
            The type of state change to initiate. Allowed values: full, config-only.
            A config-only deletion removes only the forest configuration;
            the data contained in the forest remains on disk.
            A full deletion removes both the forest configuration and the data.
        replicas : str
            Determines how to process the replicas.
            Allowed values: detach to detach the replica but keep it;
            delete to detach and delete the replica.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestDeleteCall(forest=forest, level=level, replicas=replicas)
        return self.call(call)

    def get_forest_properties(
        self,
        forest: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/forests/{id|name}/properties endpoint.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestPropertiesGetCall(forest=forest, data_format=data_format)
        return self.call(call)

    def put_forest_properties(
        self,
        forest: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/databases/{id|name}/properties endpoint.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : str | dict
            A forest properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = ForestPropertiesPutCall(forest=forest, body=body)
        return self.call(call)

    def get_roles(
        self,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles endpoint.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolesGetCall(data_format=data_format, view=view)
        return self.call(call)

    def post_roles(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/roles endpoint.

        Parameters
        ----------
        body : str | dict
            A role properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolesPostCall(body=body)
        return self.call(call)

    def get_role(
        self,
        role: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles/{id|name} endpoint.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RoleGetCall(role=role, data_format=data_format, view=view)
        return self.call(call)

    def delete_role(
        self,
        role: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/roles/{id|name} endpoint.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RoleDeleteCall(role=role)
        return self.call(call)

    def get_role_properties(
        self,
        role: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/roles/{id|name}/properties endpoint.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolePropertiesGetCall(role=role, data_format=data_format)
        return self.call(call)

    def put_role_properties(
        self,
        role: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/roles/{id|name}/properties endpoint.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        body : str | dict
            A role properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = RolePropertiesPutCall(role=role, body=body)
        return self.call(call)

    def get_users(
        self,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users endpoint.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UsersGetCall(data_format=data_format, view=view)
        return self.call(call)

    def post_users(
        self,
        body: str | dict,
    ) -> Response:
        """Send a POST request to the /manage/v2/users endpoint.

        Parameters
        ----------
        body : str | dict
            A user properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UsersPostCall(body=body)
        return self.call(call)

    def get_user(
        self,
        user: str,
        data_format: str | None = None,
        view: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users/{id|name} endpoint.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserGetCall(user=user, data_format=data_format, view=view)
        return self.call(call)

    def delete_user(
        self,
        user: str,
    ) -> Response:
        """Send a DELETE request to the /manage/v2/users/{id|name} endpoint.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserDeleteCall(user=user)
        return self.call(call)

    def get_user_properties(
        self,
        user: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/users/{id|name}/properties endpoint.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            An HTTP response
        """
        call = UserPropertiesGetCall(user=user, data_format=data_format)
        return self.call(call)

    def put_user_properties(
        self,
        user: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT request to the /manage/v2/users/{id|name}/properties endpoint.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        body : str | dict
            A user properties in XML or JSON format.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        NotImplementedError
            If the call's method is not GET, POST, PUT nor DELETE.
        """
        call = UserPropertiesPutCall(user=user, body=body)
        return self.call(call)

    def get_documents(
        self,
        uri: str | list,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        timestamp: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
    ):
        """Send a GET request to the /v1/documents endpoint.

        Parameters
        ----------
        uri : str | list
            One or more URIs for documents in the database.
            If you specify multiple URIs, the Accept header must be multipart/mixed.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str
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
        transform_params : str
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
            An HTTP response
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
        return self.call(call)

    def post_documents(
        self,
        body_parts: list[DocumentsBodyPart],
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
    ):
        """Send a POST request to the /v1/documents endpoint.

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
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : str
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
            An HTTP response
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
        return self.call(call)

    def delete_documents(
        self,
        uri: str | list,
        database: str | None = None,
        category: str | list | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        wipe_temporal: bool | None = None,
    ):
        """Send a DELETE request to the /v1/documents endpoint.

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
        return self.call(call)
