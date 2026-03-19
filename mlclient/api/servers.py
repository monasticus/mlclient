"""ServersApi - mid-level access to MarkLogic server endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import (
    ServerDeleteCall,
    ServerGetCall,
    ServerPropertiesGetCall,
    ServerPropertiesPutCall,
    ServersGetCall,
    ServersPostCall,
)

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class ServersApi:
    """Mid-level API for /manage/v2/servers endpoints."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get_list(
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
        return self._rest.call(call)

    def create(
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
        return self._rest.call(call)

    def get(
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
        return self._rest.call(call)

    def delete(
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
        return self._rest.call(call)

    def get_properties(
        self,
        server: str,
        group_id: str,
        data_format: str | None = None,
    ) -> Response:
        """Send a GET to /manage/v2/servers/{id|name}/properties.

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
        return self._rest.call(call)

    def put_properties(
        self,
        server: str,
        group_id: str,
        body: str | dict,
    ) -> Response:
        """Send a PUT to /manage/v2/servers/{id|name}/properties.

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
        return self._rest.call(call)
