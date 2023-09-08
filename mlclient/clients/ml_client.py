"""The ML Client module.

It exports 2 classes:
    * MLClient
        A low-level class used to send simple HTTP requests to a MarkLogic instance.
    * MLResourceClient
        An MLClient subclass calling ResourceCall implementation classes.
    * MLResourcesClient
        An MLResourceClient subclass supporting REST Resources of the MarkLogic server.
    * MLResponseParser
        A MarkLogic HTTP response parser.
"""
from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ElemTree
from datetime import datetime
from types import TracebackType
from typing import ClassVar

from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
from requests.auth import AuthBase, HTTPBasicAuth, HTTPDigestAuth
from requests_toolbelt import MultipartDecoder
from requests_toolbelt.multipart.decoder import BodyPart

from mlclient import constants
from mlclient.calls import (DatabaseDeleteCall, DatabaseGetCall,
                            DatabasePostCall, DatabasePropertiesGetCall,
                            DatabasePropertiesPutCall, DatabasesGetCall,
                            DatabasesPostCall, EvalCall, ForestDeleteCall,
                            ForestGetCall, ForestPostCall,
                            ForestPropertiesGetCall, ForestPropertiesPutCall,
                            ForestsGetCall, ForestsPostCall, ForestsPutCall,
                            LogsCall, ResourceCall, RoleDeleteCall,
                            RoleGetCall, RolePropertiesGetCall,
                            RolePropertiesPutCall, RolesGetCall, RolesPostCall,
                            ServerDeleteCall, ServerGetCall,
                            ServerPropertiesGetCall, ServerPropertiesPutCall,
                            ServersGetCall, ServersPostCall, UserDeleteCall,
                            UserGetCall, UserPropertiesGetCall,
                            UserPropertiesPutCall, UsersGetCall, UsersPostCall)

logger = logging.getLogger(__name__)


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

    _DEFAULT_RETRY_STRATEGY = Retry(
        connect=5,
        allowed_methods=None,  # any
        backoff_factor=0.5,
    )

    def __init__(
            self,
            protocol: str = "http",
            host: str = "localhost",
            port: int = 8002,
            auth_method: str = "basic",
            username: str = "admin",
            password: str = "admin",
            retry: Retry = _DEFAULT_RETRY_STRATEGY,
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
        retry : Retry, default Retry(connect=5,allowed_methods=None,backoff_factor=0.5)
            A retry strategy
        """
        self.protocol: str = protocol
        self.host: str = host
        self.port: int = port
        self.auth_method: str = auth_method
        self.username: str = username
        self.password: str = password
        self.base_url: str = f"{protocol}://{host}:{port}"
        self._retry: Retry = retry
        self._sess: Session | None = None
        auth_impl = HTTPBasicAuth if auth_method == "basic" else HTTPDigestAuth
        self._auth: AuthBase = auth_impl(username, password)

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
        logger.debug("Initiating a connection")
        self._sess = Session()
        self._sess.mount(self.base_url, HTTPAdapter(max_retries=self._retry))

    def disconnect(
            self,
    ):
        """Close an HTTP session."""
        if self._sess:
            logger.debug("Closing a connection")
            self._sess.close()
            self._sess = None

    def is_connected(
            self,
    ) -> bool:
        """Return a connection status.

        Returns
        -------
        bool
            True if the client has started a connection; otherwise False
        """
        return self._sess is not None

    def get(
            self,
            endpoint: str,
            params: dict | None = None,
            headers: dict | None = None,
    ) -> Response | None:
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
    ) -> Response | None:
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
    ) -> Response | None:
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
    ) -> Response | None:
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
    ):
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
        if self.is_connected():
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            request = {
                "auth": self._auth,
                "params": params,
                "headers": headers,
            }
            if body:
                content_type = headers.get(constants.HEADER_NAME_CONTENT_TYPE)
                if content_type == constants.HEADER_JSON:
                    request["json"] = body
                else:
                    request["data"] = body

            logger.debug("Sending a request... %s %s",
                         method.upper(), endpoint)
            return self._sess.request(method, url, **request)

        logger.warning("A request attempt failure: %s %s -- MLClient is not connected",
                       method.upper(), endpoint)
        return None


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
            body=call.body)


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
        call = EvalCall(xquery=xquery,
                        javascript=javascript,
                        variables=variables,
                        database=database,
                        txid=txid)
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
        call = LogsCall(filename=filename,
                        data_format=data_format,
                        host=host,
                        start_time=start_time,
                        end_time=end_time,
                        regex=regex)
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
        call = DatabasesGetCall(data_format=data_format,
                                view=view)
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
        call = DatabaseGetCall(database=database,
                               data_format=data_format,
                               view=view)
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
        call = DatabasePostCall(database=database,
                                body=body)
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
        call = DatabaseDeleteCall(database=database,
                                  forest_delete=forest_delete)
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
        call = DatabasePropertiesGetCall(database=database,
                                         data_format=data_format)
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
        call = DatabasePropertiesPutCall(database=database,
                                         body=body)
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
        call = ServersGetCall(data_format=data_format,
                              group_id=group_id,
                              view=view,
                              full_refs=full_refs)
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
        call = ServersPostCall(body=body,
                               group_id=group_id,
                               server_type=server_type)
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
        call = ServerGetCall(server=server,
                             group_id=group_id,
                             data_format=data_format,
                             view=view,
                             host_id=host_id,
                             full_refs=full_refs,
                             modules=modules)
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
        call = ServerDeleteCall(server=server,
                                group_id=group_id)
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
        call = ServerPropertiesGetCall(server=server,
                                       group_id=group_id,
                                       data_format=data_format)
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
        call = ServerPropertiesPutCall(server=server,
                                       group_id=group_id,
                                       body=body)
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
        call = ForestsGetCall(data_format=data_format,
                              view=view,
                              database=database,
                              group=group,
                              host=host,
                              full_refs=full_refs)
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
        call = ForestsPostCall(body=body,
                               wait_for_forest_to_mount=wait_for_forest_to_mount)
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
        call = ForestGetCall(forest=forest,
                             data_format=data_format,
                             view=view)
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
        call = ForestPostCall(forest=forest,
                              body=body)
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
        call = ForestDeleteCall(forest=forest,
                                level=level,
                                replicas=replicas)
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
        call = ForestPropertiesGetCall(forest=forest,
                                       data_format=data_format)
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
        call = ForestPropertiesPutCall(forest=forest,
                                       body=body)
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
        call = RolesGetCall(data_format=data_format,
                            view=view)
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
        call = RoleGetCall(role=role,
                           data_format=data_format,
                           view=view)
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
        call = RolePropertiesGetCall(role=role,
                                     data_format=data_format)
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
        call = RolePropertiesPutCall(role=role,
                                     body=body)
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
        call = UsersGetCall(data_format=data_format,
                            view=view)
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
        call = UserGetCall(user=user,
                           data_format=data_format,
                           view=view)
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
        call = UserPropertiesGetCall(user=user,
                                     data_format=data_format)
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
        call = UserPropertiesPutCall(user=user,
                                     body=body)
        return self.call(call)

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
            body=call.body)


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
        constants.HEADER_PRIMITIVE_STRING:
            lambda data: data,
        constants.HEADER_PRIMITIVE_INTEGER:
            lambda data: int(data),
        constants.HEADER_PRIMITIVE_DECIMAL:
            lambda data: float(data),
        constants.HEADER_PRIMITIVE_BOOLEAN:
            lambda data: bool(data),
        constants.HEADER_PRIMITIVE_DATE:
            lambda data: datetime.strptime(data, "%Y-%m-%d%z").date(),
        constants.HEADER_PRIMITIVE_DATE_TIME:
            lambda data: datetime.strptime(data, "%Y-%m-%dT%H:%M:%S.%f%z"),
    }

    @classmethod
    def parse(
            cls,
            response: Response,
            raw: bool = False,
    ) -> (bytes | str | int | float | bool | dict |
          ElemTree.ElementTree | ElemTree.Element |
          list):
        """Parse MarkLogic HTTP Response.

        Parameters
        ----------
        response : Response
            An HTTP response taken from MarkLogic instance
        raw : bool, default False
            If True, body parts are parsed to string

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list
            A parsed response body
        """
        if not response.ok:
            return cls._parse_error(response)
        if int(response.headers.get("Content-Length")) == 0:
            return []

        raw_parts = MultipartDecoder.from_response(response).parts
        parsed_parts = [cls._parse_part(raw_part, raw) for raw_part in raw_parts]
        if len(parsed_parts) == 1:
            return parsed_parts[0]
        return parsed_parts

    @classmethod
    def _parse_error(
            cls,
            response: Response,
    ) -> str:
        """Parse MarkLogic error response.

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
        terms = html.findall("{http://www.w3.org/1999/xhtml}body/"
                             "{http://www.w3.org/1999/xhtml}span/"
                             "{http://www.w3.org/1999/xhtml}dl/"
                             "{http://www.w3.org/1999/xhtml}dt")
        return "\n".join(term.text for term in terms)

    @classmethod
    def _parse_part(
            cls,
            raw_part: BodyPart,
            raw: bool,
    ) -> (bytes | str | int | float | bool | dict |
          ElemTree.ElementTree | ElemTree.Element |
          list):
        """Parse MarkLogic HTTP Response part.

        Parameters
        ----------
        raw_part : BodyPart
            An HTTP response part taken from MarkLogic instance
        raw : bool
            If True, body parts are parsed to string

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list
            A parsed response body part
        """
        text = raw_part.text
        if raw:
            return text

        content_type = cls._get_header(raw_part, constants.HEADER_NAME_CONTENT_TYPE)
        primitive_type = cls._get_header(raw_part, constants.HEADER_NAME_PRIMITIVE)
        if (content_type == constants.HEADER_PLAIN_TEXT and
                primitive_type in cls._PLAIN_TEXT_PARSERS):
            return cls._PLAIN_TEXT_PARSERS[primitive_type](text)
        if content_type == constants.HEADER_JSON:
            return json.loads(text)
        if content_type == constants.HEADER_XML:
            element = ElemTree.fromstring(text)
            if primitive_type == constants.HEADER_PRIMITIVE_DOCUMENT_NODE:
                return ElemTree.ElementTree(element)
            return element

        return raw_part.content

    @staticmethod
    def _get_header(
            raw_part: BodyPart,
            header_name: str,
    ) -> str:
        """Return a header value of response body part.

        All headers are stored in a binary form. This method decodes them using
        BodyPart's encoding attribute.

        Parameters
        ----------
        raw_part : BodyPart
            A response body part
        header_name : str
            A header name

        Returns
        -------
        str
            A header value
        """
        encoded_header_name = header_name.encode(raw_part.encoding)
        header_value = raw_part.headers.get(encoded_header_name)
        return header_value.decode(raw_part.encoding)
