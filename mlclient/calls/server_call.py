from mlclient import exceptions, utils
from mlclient.calls import ResourceCall


class ServerGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request to the /manage/v2/servers/{id|name} REST Resource

    This resource address returns data about a specific App Server.
    The server can be identified either by id or name.
    The data returned depends on the value of the view request parameter.
    The default view is a summary with links to additional data.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/servers/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
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

    def __init__(self, server: str, group_id: str, data_format: str = "xml", view: str = "default",
                 host_id: str = None, full_refs: bool = None, modules: bool = None):
        """
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
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        ServerGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__server = server
        self.add_param(ServerGetCall.__GROUP_ID_PARAM, group_id)
        self.add_param(ServerGetCall.__FORMAT_PARAM, data_format)
        self.add_param(ServerGetCall.__VIEW_PARAM, view)
        self.add_param(ServerGetCall.__HOST_ID_PARAM, host_id)
        self.add_param(ServerGetCall.__FULL_REFS_PARAM, str(full_refs).lower() if full_refs is not None else None)
        self.add_param(ServerGetCall.__MODULES_PARAM, str(modules).lower() if modules is not None else None)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Server call

        Returns
        -------
        str
            an Server call endpoint
        """

        return ServerGetCall.__ENDPOINT_TEMPLATE.format(self.__server)

    @staticmethod
    def __validate_params(data_format: str, view: str):
        if data_format not in ServerGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(ServerGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)
        if view not in ServerGetCall.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(ServerGetCall.__SUPPORTED_VIEWS)
            raise exceptions.WrongParameters("The supported views are: " + joined_supported_views)


class ServerDeleteCall(ResourceCall):
    """
    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/servers/{id|name} REST Resource

    This resource address deletes the specified App Server from the specified group.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/servers/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/servers/{}"

    __GROUP_ID_PARAM = "group-id"

    def __init__(self, server: str, group_id: str):
        """
        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.
        """
        super().__init__(method="DELETE")
        self.add_param(ServerDeleteCall.__GROUP_ID_PARAM, group_id)
        self.__server = server

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Server call

        Returns
        -------
        str
            an Server call endpoint
        """

        return ServerDeleteCall.__ENDPOINT_TEMPLATE.format(self.__server)
