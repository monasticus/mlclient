import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ServersGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request to the /manage/v2/servers REST Resource

    This resource address returns data about the App Servers in the cluster.
    The data returned depends on the setting of the view request parameter.
    The default view provides a summary of the servers.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/servers

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Servers endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/manage/v2/servers"

    __FORMAT_PARAM = "format"
    __GROUP_ID_PARAM = "group-id"
    __VIEW_PARAM = "view"
    __FULL_REFS_PARAM = "fullrefs"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "status", "metrics", "package", "schema", "properties-schema"]

    def __init__(self, data_format: str = "xml", group_id: str = None, view: str = "default", full_refs: bool = None):
        """
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
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        ServersGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.add_param(ServersGetCall.__FORMAT_PARAM, data_format)
        self.add_param(ServersGetCall.__GROUP_ID_PARAM, group_id)
        self.add_param(ServersGetCall.__VIEW_PARAM, view)
        self.add_param(ServersGetCall.__FULL_REFS_PARAM, str(full_refs).lower() if full_refs is not None else None)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Servers call

        Returns
        -------
        str
            an Servers call endpoint
        """

        return ServersGetCall.ENDPOINT

    @staticmethod
    def __validate_params(data_format: str, view: str):
        if data_format not in ServersGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(ServersGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)
        if view not in ServersGetCall.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(ServersGetCall.__SUPPORTED_VIEWS)
            raise exceptions.WrongParameters("The supported views are: " + joined_supported_views)


class ServersPostCall(ResourceCall):
    """
    A ResourceCall implementation representing a single POST request to the /manage/v2/servers REST Resource

    This resource address is used to create a new App Server in the specified group.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/servers

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Servers endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/manage/v2/servers"

    __GROUP_ID_PARAM = "group-id"
    __SERVER_TYPE_PARAM = "server-type"

    __SUPPORTED_SERVER_TYPES = ["http", "odbc", "xdbc", "webdav"]

    def __init__(self, body: Union[str, dict], group_id: str = None, server_type: str = None):
        """
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
        """
        ServersPostCall.__validate_params(server_type, body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)
        self.add_param(ServersPostCall.__GROUP_ID_PARAM, group_id)
        self.add_param(ServersPostCall.__SERVER_TYPE_PARAM, server_type)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Servers call

        Returns
        -------
        str
            an Servers call endpoint
        """

        return ServersPostCall.ENDPOINT

    @staticmethod
    def __validate_params(server_type: str, body: Union[str, dict]):
        if server_type and server_type not in ServersPostCall.__SUPPORTED_SERVER_TYPES:
            joined_supported_server_types = ", ".join(ServersPostCall.__SUPPORTED_SERVER_TYPES)
            raise exceptions.WrongParameters("The supported server types are: " + joined_supported_server_types)
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            raise exceptions.WrongParameters("No request body provided for POST /manage/v2/servers!")
