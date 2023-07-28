"""The ML Server Resource Calls module.

It exports 2 classes:
* ServerGetCall
    A GET request to get app server details.
* ServerDeleteCall
    A DELETE request to remove an app server.
"""
from __future__ import annotations

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ServerGetCall(ResourceCall):
    """A GET request to get app server details.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/servers/{id|name} REST Resource.

    This resource address returns data about a specific App Server.
    The server can be identified either by id or name.
    The data returned depends on the value of the view request parameter.
    The default view is a summary with links to additional data.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/servers/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/servers/{}"

    __GROUP_ID_PARAM = "group-id"
    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"
    __HOST_ID_PARAM = "host-id"
    __FULL_REFS_PARAM = "fullrefs"
    __MODULES_PARAM = "modules"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "config", "edit", "package",
                         "status", "xdmp:server-status", "properties-schema"]

    def __init__(
            self, server: str,
            group_id: str,
            data_format: str = "xml",
            view: str = "default",
            host_id: str = None,
            full_refs: bool = None,
            modules: bool = None
    ):
        """Initialize ServerGetCall instance.

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
            Meaningful only when view=status. Specifies to return the status for
            the server in the specified host. The host can be identified either by id
            or name.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for
            first references. This parameter is not meaningful with view=package.
        modules : bool
            Meaningful only with view=package. Whether to include a manifest
            of the modules database for the App Server in the results, if one exists.
            It is an error to request a modules database manifest for an App Server
            that uses the filesystem for modules. Default: false.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        ServerGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        if full_refs is not None:
            full_refs = str(full_refs).lower()
        if modules is not None:
            modules = str(modules).lower()
        self.__server = server
        self.add_param(ServerGetCall.__GROUP_ID_PARAM, group_id)
        self.add_param(ServerGetCall.__FORMAT_PARAM, data_format)
        self.add_param(ServerGetCall.__VIEW_PARAM, view)
        self.add_param(ServerGetCall.__HOST_ID_PARAM, host_id)
        self.add_param(ServerGetCall.__FULL_REFS_PARAM, full_refs)
        self.add_param(ServerGetCall.__MODULES_PARAM, modules)

    def endpoint(
            self
    ):
        """Return an endpoint for the Server call.

        Returns
        -------
        str
            A Server call endpoint
        """
        return ServerGetCall.__ENDPOINT_TEMPLATE.format(self.__server)

    @classmethod
    def __validate_params(
            cls,
            data_format: str,
            view: str
    ):
        if data_format not in cls.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls.__SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if view not in cls.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(cls.__SUPPORTED_VIEWS)
            msg = f"The supported views are: {joined_supported_views}"
            raise exceptions.WrongParametersError(msg)


class ServerDeleteCall(ResourceCall):
    """A DELETE request to remove an app server.

    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/servers/{id|name} REST Resource.

    This resource address deletes the specified App Server from the specified group.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/servers/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/servers/{}"

    __GROUP_ID_PARAM = "group-id"

    def __init__(
            self,
            server: str,
            group_id: str
    ):
        """Initialize ServerDeleteCall instance.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self.add_param(ServerDeleteCall.__GROUP_ID_PARAM, group_id)
        self.__server = server

    def endpoint(
            self
    ):
        """Return an endpoint for the Server call.

        Returns
        -------
        str
            A Server call endpoint
        """
        return ServerDeleteCall.__ENDPOINT_TEMPLATE.format(self.__server)
