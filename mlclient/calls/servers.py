"""The ML Server Resource Calls module.

This module provides call classes for server-related REST resources.

It exports 6 classes:
    * ServersGetCall
        A GET request to get app servers summary.
    * ServersPostCall
        A POST request to create a new app server.
    * ServerGetCall
        A GET request to get app server details.
    * ServerDeleteCall
        A DELETE request to remove an app server.
    * ServerPropertiesGetCall
        A GET request to get app server properties.
    * ServerPropertiesPutCall
        A PUT request to modify app server properties.
"""

from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import RestCall


class ServersGetCall(RestCall):
    """A GET request to get app servers summary.

    A RestCall implementation representing a single GET request
    to the /manage/v2/servers REST Resource.

    This resource address returns data about the App Servers in the cluster.
    The data returned depends on the setting of the view request parameter.
    The default view provides a summary of the servers.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/servers
    """

    _ENDPOINT: str = "/manage/v2/servers"

    _FORMAT_PARAM: str = "format"
    _GROUP_ID_PARAM: str = "group-id"
    _VIEW_PARAM: str = "view"
    _FULL_REFS_PARAM: str = "fullrefs"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = [
        "describe",
        "default",
        "status",
        "metrics",
        "package",
        "schema",
        "properties-schema",
    ]

    def __init__(
        self,
        data_format: str = "xml",
        group_id: str | None = None,
        view: str = "default",
        full_refs: bool | None = None,
    ):
        """Initialize ServersGetCall instance.

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
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        if full_refs is not None:
            full_refs = str(full_refs).lower()
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._VIEW_PARAM, view)
        self.add_param(self._FULL_REFS_PARAM, full_refs)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Servers call.

        Returns
        -------
        str
            A Servers call endpoint
        """
        return self._ENDPOINT

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


class ServersPostCall(RestCall):
    """A POST request to create a new app server.

    A RestCall implementation representing a single POST request
    to the /manage/v2/servers REST Resource.

    This resource address is used to create a new App Server in the specified group.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/servers
    """

    _ENDPOINT: str = "/manage/v2/servers"

    _GROUP_ID_PARAM: str = "group-id"
    _SERVER_TYPE_PARAM: str = "server-type"

    _SUPPORTED_SERVER_TYPES: ClassVar[list] = ["http", "odbc", "xdbc", "webdav"]

    def __init__(
        self,
        body: str | dict,
        group_id: str | None = None,
        server_type: str | None = None,
    ):
        """Initialize ServersPostCall instance.

        Parameters
        ----------
        body : str | dict
            A server properties in XML or JSON format.
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
        """
        self._validate_params(server_type, body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="POST", content_type=content_type, body=body)
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._SERVER_TYPE_PARAM, server_type)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Servers call.

        Returns
        -------
        str
            A Servers call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
        cls,
        server_type: str,
        body: str | dict,
    ):
        if server_type and server_type not in cls._SUPPORTED_SERVER_TYPES:
            joined_supported_server_types = ", ".join(cls._SUPPORTED_SERVER_TYPES)
            msg = f"The supported server types are: {joined_supported_server_types}"
            raise exceptions.WrongParametersError(msg)
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = "No request body provided for POST /manage/v2/servers!"
            raise exceptions.WrongParametersError(msg)


class ServerGetCall(RestCall):
    """A GET request to get app server details.

    A RestCall implementation representing a single GET request
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
    _SUPPORTED_VIEWS: ClassVar[list] = [
        "describe",
        "default",
        "config",
        "edit",
        "package",
        "status",
        "xdmp:server-status",
        "properties-schema",
    ]

    def __init__(
        self,
        server: str,
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

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
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


class ServerDeleteCall(RestCall):
    """A DELETE request to remove an app server.

    A RestCall implementation representing a single DELETE request
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


class ServerPropertiesGetCall(RestCall):
    """A GET request to get app server properties.

    A RestCall implementation representing a single GET request
    to the /manage/v2/servers/{id|name}/properties REST Resource.

    This resource address returns the current state of modifiable properties
    of the specified App Server.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/servers/[id-or-name]/properties
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/servers/{}/properties"

    _GROUP_ID_PARAM: str = "group-id"
    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        server: str,
        group_id: str,
        data_format: str = "xml",
    ):
        """Initialize ServerPropertiesGetCall instance.

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
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._server = server
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Server Properties call.

        Returns
        -------
        str
            A Server Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._server)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class ServerPropertiesPutCall(RestCall):
    """A PUT request to modify app server properties.

    A RestCall implementation representing a single PUT request
    to the /manage/v2/servers/{id|name}/properties REST Resource.

    Initiate a properties change on the specified App Server.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/servers/[id-or-name]/properties
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/servers/{}/properties"

    _GROUP_ID_PARAM: str = "group-id"

    def __init__(
        self,
        server: str,
        group_id: str,
        body: str | dict,
    ):
        """Initialize ServerPropertiesPutCall instance.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        body : str | dict
            A server properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT", content_type=content_type, body=body)
        self._server = server
        self.add_param(self._GROUP_ID_PARAM, group_id)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Server Properties call.

        Returns
        -------
        str
            A Server Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._server)

    @classmethod
    def _validate_params(
        cls,
        body: str | dict,
    ):
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = (
                "No request body provided for "
                "PUT /manage/v2/servers/{id|name}/properties!"
            )
            raise exceptions.WrongParametersError(msg)
