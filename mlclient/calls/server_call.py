"""The ML Server Resource Calls module.

It exports 2 classes:
    * ServerGetCall
        A GET request to get app server details.
    * ServerDeleteCall
        A DELETE request to remove an app server.
"""
from __future__ import annotations

from typing import ClassVar

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
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/servers/{}"

    _GROUP_ID_PARAM: str = "group-id"
    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"
    _HOST_ID_PARAM: str = "host-id"
    _FULL_REFS_PARAM: str = "fullrefs"
    _MODULES_PARAM: str = "modules"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default", "config", "edit",
                                        "package", "status", "xdmp:server-status",
                                        "properties-schema"]

    def __init__(
            self, server: str,
            group_id: str,
            data_format: str = "xml",
            view: str = "default",
            host_id: str | None = None,
            full_refs: bool | None = None,
            modules: bool | None = None,
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
        self._validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        if full_refs is not None:
            full_refs = str(full_refs).lower()
        if modules is not None:
            modules = str(modules).lower()
        self._server = server
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)
        self.add_param(self._HOST_ID_PARAM, host_id)
        self.add_param(self._FULL_REFS_PARAM, full_refs)
        self.add_param(self._MODULES_PARAM, modules)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Server call.

        Returns
        -------
        str
            A Server call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._server)

    @classmethod
    def _validate_params(
            cls,
            data_format: str,
            view: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if view not in cls._SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(cls._SUPPORTED_VIEWS)
            msg = f"The supported views are: {joined_supported_views}"
            raise exceptions.WrongParametersError(msg)


class ServerDeleteCall(ResourceCall):
    """A DELETE request to remove an app server.

    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/servers/{id|name} REST Resource.

    This resource address deletes the specified App Server from the specified group.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/servers/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/servers/{}"

    _GROUP_ID_PARAM: str = "group-id"

    def __init__(
            self,
            server: str,
            group_id: str,
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
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self._server = server

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Server call.

        Returns
        -------
        str
            A Server call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._server)
