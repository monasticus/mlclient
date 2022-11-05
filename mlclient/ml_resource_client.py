from typing import Union

from requests import Response

from mlclient import MLClient, constants
from mlclient.calls import (DatabaseDeleteCall, DatabaseGetCall,
                            DatabasePostCall, DatabasePropertiesGetCall,
                            DatabasePropertiesPutCall, DatabasesGetCall,
                            DatabasesPostCall, EvalCall, LogsCall,
                            ResourceCall, ServerDeleteCall, ServerGetCall,
                            ServerPropertiesGetCall, ServerPropertiesPutCall,
                            ServersGetCall, ServersPostCall)


class MLResourceClient(MLClient):
    """
    This class extends the MLClient superclass to support internal REST Resources of the MarkLogic server.

    It can connect with the MarkLogic Server as a Context Manager or explicitly by
    using the connect method.

    There are two ways to call ML REST Resources:
    - by using defined methods corresponding to a resource (e.g. /v1/eval -> eval())
    - by using a general method call() accepting a ResourceCall implementation classes.

    This class can be treated as an example of MLClient class extension for your own dedicated APIs
    or as a superclass for your client.

    Attributes
    -------
    All attributes are inherited from the MLClient superclass.

    Methods
    -------
    MLResourceClient inherits all MLClient methods: connect, disconnect, is_connected, get, post, put, delete.

    eval(xquery: str = None, javascript: str = None, variables: dict = None,
         database: str = None, txid: str = None) -> Response
        Sends a request to the /v1/eval REST Resource using EvalCall class
    get_logs(filename: str, data_format: str = None, host: str = None,
             start_time: str = None, end_time: str = None, regex: str = None) -> Response
        Sends a request to the /manage/v2/logs REST Resource using LogsCall class
    get_databases(data_format: str = None, view: str = None) -> Response
        Sends a request to the /manage/v2/databases REST Resource using DatabasesGetCall class
    post_databases(body: Union[str, dict]) -> Response
        Sends a request to the /manage/v2/databases REST Resource using DatabasesPostCall class
    get_database(database: str, data_format: str = None, view: str = None) -> Response
        Sends a request to the /manage/v2/databases/{id|name} REST Resource using DatabaseGetCall class
    post_database(database: str, body: Union[str, dict]) -> Response
        Sends a request to the /manage/v2/databases/{id|name} REST Resource using DatabasePostCall class
    delete_database(database: str, forest_delete: str = None) -> Response
        Sends a request to the /manage/v2/databases/{id|name} REST Resource using DatabaseDeleteCall class
    get_database_properties(database: str, data_format: str = None) -> Response
        Sends a request to the /manage/v2/databases/{id|name}/properties REST Resource
        using DatabasePropertiesGetCall class
    put_database_properties(database: str, body: Union[str, dict]) -> Response
        Sends a request to the /manage/v2/databases/{id|name}/properties REST Resource
        using DatabasePropertiesPutCall class
    get_servers(data_format: str = None, group_id: str = None, view: str = None, full_refs: bool = None) -> Response
        Sends a request to the /manage/v2/servers REST Resource using ServersGetCall class
    post_servers(body: Union[str, dict], group_id: str = None, server_type: str = None) -> Response
        Sends a request to the /manage/v2/servers REST Resource using ServersPostCall class
    get_server(server: str, group_id: str, data_format: str = None, view: str = None,
               host_id: str = None, full_refs: bool = None, modules: bool = None) -> Response
        Sends a request to the /manage/v2/servers/{id|name} REST Resource using ServerGetCall class
    delete_server(server: str, group_id: str) -> Response
        Sends a request to the /manage/v2/servers/{id|name} REST Resource using ServerDeleteCall class
    get_server_properties(server: str, group_id: str, data_format: str = None) -> Response
        Sends a request to the /manage/v2/servers/{id|name}/properties REST Resource
        using ServerPropertiesGetCall class
    put_server_properties(server: str, group_id: str, body: Union[str, dict]) -> Response
        Sends a request to the /manage/v2/servers/{id|name}/properties REST Resource
        using ServerPropertiesPutCall class
    call(call: ResourceCall) -> Response
        Sends a custom request to a MarkLogic endpoint using a ResourceCall implementation
    """

    def eval(self, xquery: str = None, javascript: str = None, variables: dict = None,
             database: str = None, txid: str = None) -> Response:
        """
        Sends a request to the /v1/eval REST Resource using EvalCall class

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
            instead of the default content database associated with the REST API instance.
            The database can be identified by name or by database id.
        txid
            The transaction identifier of the multi-statement transaction
            in which to service this request.

        Returns
        -------
        Response
            an HTTP response
        """

        call = EvalCall(xquery=xquery,
                        javascript=javascript,
                        variables=variables,
                        database=database,
                        txid=txid)
        return self.call(call)

    def get_logs(self, filename: str, data_format: str = None, host: str = None,
                 start_time: str = None, end_time: str = None, regex: str = None) -> Response:
        """
        Sends a request to the /manage/v2/logs REST Resource using LogsCall class

        Parameters
        ----------
        filename : str
            The log file to be returned.
        data_format : str
            The format of the data in the log file. The supported formats are xml, json or html.
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
            an HTTP response
        """

        call = LogsCall(filename=filename,
                        data_format=data_format,
                        host=host,
                        start_time=start_time,
                        end_time=end_time,
                        regex=regex)
        return self.call(call)

    def get_databases(self, data_format: str = None, view: str = None) -> Response:
        """
        Sends a request to the /manage/v2/databases REST Resource using DatabasesGetCall class

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
            an HTTP response
        """

        call = DatabasesGetCall(data_format=data_format,
                                view=view)
        return self.call(call)

    def post_databases(self, body: Union[str, dict]) -> Response:
        """
        Sends a request to the /manage/v2/databases REST Resource using DatabasesPostCall class

        Parameters
        ----------
        body : Union[str, dict]
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            an HTTP response
        """

        call = DatabasesPostCall(body=body)
        return self.call(call)

    def get_database(self, database: str, data_format: str = None, view: str = None) -> Response:
        """
        Sends a request to the /manage/v2/databases/{id|name} REST Resource using DatabaseGetCall class

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data.
            Can be properties-schema, package, describe, config, counts, edit, status, forest-storage, or default.

        Returns
        -------
        Response
            an HTTP response
        """

        call = DatabaseGetCall(database=database,
                               data_format=data_format,
                               view=view)
        return self.call(call)

    def post_database(self, database: str, body: Union[str, dict]) -> Response:
        """
        Sends a request to the /manage/v2/databases/{id|name} REST Resource using DatabasePostCall class

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : Union[str, dict]
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            an HTTP response
        """

        call = DatabasePostCall(database=database,
                                body=body)
        return self.call(call)

    def delete_database(self, database: str, forest_delete: str = None) -> Response:
        """
        Sends a request to the /manage/v2/databases/{id|name} REST Resource using DatabaseDeleteCall class

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
            an HTTP response
        """

        call = DatabaseDeleteCall(database=database,
                                  forest_delete=forest_delete)
        return self.call(call)

    def get_database_properties(self, database: str, data_format: str = None) -> Response:
        """
        Sends a request to the /manage/v2/databases/{id|name}/properties REST Resource
        using DatabasePropertiesGetCall class

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
            an HTTP response
        """

        call = DatabasePropertiesGetCall(database=database,
                                         data_format=data_format)
        return self.call(call)

    def put_database_properties(self, database: str, body: Union[str, dict]) -> Response:
        """
        Sends a request to the /manage/v2/databases/{id|name}/properties REST Resource
        using DatabasePropertiesPutCall class

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : Union[str, dict]
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            an HTTP response
        """

        call = DatabasePropertiesPutCall(database=database,
                                         body=body)
        return self.call(call)

    def get_servers(self, data_format: str = None, group_id: str = None, view: str = None,
                    full_refs: bool = None) -> Response:
        """
        Sends a request to the /manage/v2/servers REST Resource using ServersGetCall class

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
            A value of false (the default) indicates to return detail only for first references.
            This parameter is not meaningful with view=package.

        Returns
        -------
        Response
            an HTTP response
        """

        call = ServersGetCall(data_format=data_format,
                              group_id=group_id,
                              view=view,
                              full_refs=full_refs)
        return self.call(call)

    def post_servers(self, body: Union[str, dict], group_id: str = None, server_type: str = None) -> Response:
        """
        Sends a request to the /manage/v2/servers REST Resource using ServersPostCall class

        Parameters
        ----------
        body : Union[str, dict]
            A database properties in XML or JSON format.
        group_id : str
            The id or name of the group to which the App Server belongs.
            The group must be specified by this parameter or by the group-name property in the request payload.
            If it is specified in both places, the values must be the same.
        server_type : str
            The type of App Server to create.
            The App Server type must be specified by this parameter or in the request payload.
            If it is specified in both places, the values must be the same.
            The valid types are: http, odbc, xdbc, or webdav.

        Returns
        -------
        Response
            an HTTP response
        """

        call = ServersPostCall(body=body,
                               group_id=group_id,
                               server_type=server_type)
        return self.call(call)

    def get_server(self, server: str, group_id: str, data_format: str = None, view: str = None,
                   host_id: str = None, full_refs: bool = None, modules: bool = None) -> Response:
        """
        Sends a request to the /manage/v2/servers/{id|name} REST Resource using ServerGetCall class

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be properties-schema, config, edit, package, describe, status, xdmp:server-status or default.
        host_id : str
            Meaningful only when view=status. Specifies to return the status for the server in the specified host.
            The host can be identified either by id or name.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first references.
            This parameter is not meaningful with view=package.
        modules : bool
            Meaningful only with view=package. Whether to include a manifest of the modules database
            for the App Server in the results, if one exists. It is an error to request
            a modules database manifest for an App Server that uses the filesystem for modules. Default: false.

        Returns
        -------
        Response
            an HTTP response
        """

        call = ServerGetCall(server=server,
                             group_id=group_id,
                             data_format=data_format,
                             view=view,
                             host_id=host_id,
                             full_refs=full_refs,
                             modules=modules)
        return self.call(call)

    def delete_server(self, server: str, group_id: str) -> Response:
        """
        Sends a request to the /manage/v2/servers/{id|name} REST Resource using ServerDeleteCall class

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.

        Returns
        -------
        Response
            an HTTP response
        """

        call = ServerDeleteCall(server=server,
                                group_id=group_id)
        return self.call(call)

    def get_server_properties(self, server: str, group_id: str, data_format: str = None):
        """
        Sends a request to the /manage/v2/servers/{id|name}/properties REST Resource
        using ServerPropertiesGetCall class

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.

        Returns
        -------
        Response
            an HTTP response
        """

        call = ServerPropertiesGetCall(server=server,
                                       group_id=group_id,
                                       data_format=data_format)
        return self.call(call)

    def put_server_properties(self, server: str, group_id: str, body: Union[str, dict]):
        """
        Sends a request to the /manage/v2/servers/{id|name}/properties REST Resource
        using ServerPropertiesPutCall class

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.
        body : Union[str, dict]
            A database properties in XML or JSON format.

        Returns
        -------
        Response
            an HTTP response
        """

        call = ServerPropertiesPutCall(server=server,
                                       group_id=group_id,
                                       body=body)
        return self.call(call)

    def call(self, call: ResourceCall) -> Response:
        """
        Sends a custom request to a MarkLogic endpoint using a ResourceCall implementation

        Parameters
        ----------
        call : ResourceCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            an HTTP response
        """

        method = call.method()
        if method == constants.METHOD_GET:
            return self.get(endpoint=call.endpoint(),
                            params=call.params(),
                            headers=call.headers())
        elif method == constants.METHOD_POST:
            return self.post(endpoint=call.endpoint(),
                             params=call.params(),
                             headers=call.headers(),
                             body=call.body())
        elif method == constants.METHOD_PUT:
            return self.put(endpoint=call.endpoint(),
                            params=call.params(),
                            headers=call.headers(),
                            body=call.body())
        elif method == constants.METHOD_DELETE:
            return self.delete(endpoint=call.endpoint(),
                               params=call.params(),
                               headers=call.headers())
