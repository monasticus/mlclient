"""Admin API group for /admin/v1/* endpoints (AdminApi / AsyncAdminApi).

Requires the Admin server (port 8001 by default).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.admin import (
    ClusterConfigPostCall,
    HostConfigDeleteCall,
    InitPostCall,
    InstanceAdminPostCall,
    ServerConfigGetCall,
    TimestampGetCall,
    TimestampHeadCall,
)
from mlclient.calls.base import ApiCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class AdminApi:
    """Admin API group for /admin/v1/* endpoints.

    Requires the Admin server (port 8001 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self._api.call(call_, timeout=timeout)

    def get_timestamp(self, *, timeout=UNSET) -> Response:
        """Verify that MarkLogic Server is up and accepting requests.

        Returns a plain text timestamp of the last restart. Can be used to
        detect when a restart triggered by an administrative operation has
        completed.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/timestamp

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``text/plain`` body containing the timestamp

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self._api.call(TimestampGetCall(), timeout=timeout)

    def head_timestamp(self, *, timeout=UNSET) -> Response:
        """Verify that MarkLogic Server is up and accepting requests.

        A lightweight availability check: the response carries only a status
        code, 200 (OK) when the server is available, and no body.

        Documentation: https://docs.marklogic.com/REST/HEAD/admin/v1/timestamp

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response without a body

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self._api.call(TimestampHeadCall(), timeout=timeout)

    def get_server_config(self, *, timeout=UNSET) -> Response:
        """Retrieve server configuration information for cluster join.

        Returns the host configuration as XML, suitable for use as input to
        ``POST /admin/v1/cluster-config`` when adding this host to a cluster.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/server-config

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``application/xml`` body containing
            the server configuration

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self._api.call(ServerConfigGetCall(), timeout=timeout)

    def post_init(
        self,
        *,
        body: str | dict | None = None,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Initialize MarkLogic Server.

        Must be the first call when setting up an instance; the instance is
        fully initialized only after post_instance_admin or a cluster join. On
        an initialized instance it only installs the license given, if any.
        A restart is not awaited: compare get_timestamp before and after.

        Documentation: https://docs.marklogic.com/REST/POST/admin/v1/init

        Parameters
        ----------
        body : str | dict | None
            A license to install in XML or JSON format, with the license-key and
            licensee properties. Without a body the server is initialized without
            installing a license.
        data_format : str | None
            The expected format of the data in the response body.
            Allowed values: json or xml. If present, this parameter overrides
            the Accept header.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp and Location
            when the server initializes, 204 when it was already initialized

        Raises
        ------
        WrongParametersError
            If the format is unsupported, or the body is blank or a JSON
            value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = InitPostCall(body=body, data_format=data_format)
        return self._api.call(call, timeout=timeout)

    def post_instance_admin(
        self,
        body: str | dict,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Install the admin user and initialize security.

        Use it on a standalone host or the bootstrap host of a cluster, after
        post_init. Initialization cannot be repeated. The restart it causes
        is not awaited.

        Documentation: https://docs.marklogic.com/REST/POST/admin/v1/instance-admin

        Parameters
        ----------
        body : str | dict
            The admin user in XML or JSON format. The admin-username and
            admin-password properties are required; wallet-password (defaults to
            the admin password) and realm are optional.
        data_format : str | None
            The format of the data in the response body.
            Allowed values: json or xml. If present, this parameter overrides
            the Accept header.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp and Location

        Raises
        ------
        WrongParametersError
            If the format is unsupported, or the body is missing, blank or a
            JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = InstanceAdminPostCall(body=body, data_format=data_format)
        return self._api.call(call, timeout=timeout)

    def post_cluster_config(
        self,
        *,
        server_config: str | None = None,
        group: str | None = None,
        zone: str | None = None,
        cluster_config: bytes | None = None,
        timeout=UNSET,
    ) -> Response:
        """Exchange the configuration for a cluster join.

        Joining a host takes two requests: send the joining host's
        get_server_config output with its group to a host of the cluster, then
        send the returned ZIP archive as cluster_config to the joining host,
        which restarts. Include either server_config or cluster_config. Send the
        archive only to the joining host: MarkLogic Server 12.1 also accepts it
        on an initialized host and replaces that host's cluster configuration.

        Documentation: https://docs.marklogic.com/REST/POST/admin/v1/cluster-config

        Parameters
        ----------
        server_config : str | None
            The server configuration of a new host to be joined to this cluster.
            Its value should be the output of a previous call to
            GET /admin/v1/server-config. Sent as form data in the request body.
            You must include either this parameter or the cluster_config
            parameter, but not both.
        group : str | None
            The group of the new host. Required with the server_config parameter,
            not permitted otherwise.
        zone : str | None
            Optional text describing the location of the new host, such as the
            name of an Amazon EC2 Availability Zone. Used by the Tiered Storage
            API to configure local disk failover. Permitted only with the
            server_config parameter.
        cluster_config : bytes | None
            The cluster configuration in ZIP format, as returned by a previous
            request with the server_config parameter. Sent to the joining host
            to complete the cluster join. You must include either this parameter
            or the server_config parameter, but not both.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 200 with the cluster configuration ZIP archive
            for a server_config request, 202 with a restart timestamp for a
            cluster_config request

        Raises
        ------
        WrongParametersError
            If neither or both of server_config and cluster_config are given,
            server_config is given without group, or group or zone is given
            with cluster_config.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ClusterConfigPostCall(
            server_config=server_config,
            group=group,
            zone=zone,
            cluster_config=cluster_config,
        )
        return self._api.call(call, timeout=timeout)

    def delete_host_config(
        self,
        *,
        remote_host: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Drop a host from the cluster.

        The host must have no forests and must not be a replication bootstrap
        or shared disk failover host. Without remote_host the receiving host
        removes itself and restarts uninitialized; with it, the receiving host
        drops the remote host, which is no longer a viable instance.

        Documentation: https://docs.marklogic.com/REST/DELETE/admin/v1/host-config

        Parameters
        ----------
        remote_host : str | None
            Request a host in a cluster to remove the host referenced by this
            parameter. To request a host to remove itself, omit this parameter.
            The hostname must be resolvable on the host that receives the
            request. The remote host can be in any group in the cluster.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp when a host
            removes itself, 204 when it removes a remote host

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostConfigDeleteCall(remote_host=remote_host)
        return self._api.call(call, timeout=timeout)


class AsyncAdminApi:
    """Async Admin API group for /admin/v1/* endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self._api.call(call_, timeout=timeout)

    async def get_timestamp(self, *, timeout=UNSET) -> Response:
        """Verify that MarkLogic Server is up and accepting requests.

        Returns a plain text timestamp of the last restart. Can be used to
        detect when a restart triggered by an administrative operation has
        completed.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/timestamp

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``text/plain`` body containing the timestamp

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self._api.call(TimestampGetCall(), timeout=timeout)

    async def head_timestamp(self, *, timeout=UNSET) -> Response:
        """Verify that MarkLogic Server is up and accepting requests.

        A lightweight availability check: the response carries only a status
        code, 200 (OK) when the server is available, and no body.

        Documentation: https://docs.marklogic.com/REST/HEAD/admin/v1/timestamp

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response without a body

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self._api.call(TimestampHeadCall(), timeout=timeout)

    async def get_server_config(self, *, timeout=UNSET) -> Response:
        """Retrieve server configuration information for cluster join.

        Returns the host configuration as XML, suitable for use as input to
        ``POST /admin/v1/cluster-config`` when adding this host to a cluster.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/server-config

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``application/xml`` body containing
            the server configuration

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self._api.call(ServerConfigGetCall(), timeout=timeout)

    async def post_init(
        self,
        *,
        body: str | dict | None = None,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Initialize MarkLogic Server.

        Must be the first call when setting up an instance; the instance is
        fully initialized only after post_instance_admin or a cluster join. On
        an initialized instance it only installs the license given, if any.
        A restart is not awaited: compare get_timestamp before and after.

        Documentation: https://docs.marklogic.com/REST/POST/admin/v1/init

        Parameters
        ----------
        body : str | dict | None
            A license to install in XML or JSON format, with the license-key and
            licensee properties. Without a body the server is initialized without
            installing a license.
        data_format : str | None
            The expected format of the data in the response body.
            Allowed values: json or xml. If present, this parameter overrides
            the Accept header.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp and Location
            when the server initializes, 204 when it was already initialized

        Raises
        ------
        WrongParametersError
            If the format is unsupported, or the body is blank or a JSON
            value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = InitPostCall(body=body, data_format=data_format)
        return await self._api.call(call, timeout=timeout)

    async def post_instance_admin(
        self,
        body: str | dict,
        *,
        data_format: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Install the admin user and initialize security.

        Use it on a standalone host or the bootstrap host of a cluster, after
        post_init. Initialization cannot be repeated. The restart it causes
        is not awaited.

        Documentation: https://docs.marklogic.com/REST/POST/admin/v1/instance-admin

        Parameters
        ----------
        body : str | dict
            The admin user in XML or JSON format. The admin-username and
            admin-password properties are required; wallet-password (defaults to
            the admin password) and realm are optional.
        data_format : str | None
            The format of the data in the response body.
            Allowed values: json or xml. If present, this parameter overrides
            the Accept header.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp and Location

        Raises
        ------
        WrongParametersError
            If the format is unsupported, or the body is missing, blank or a
            JSON value other than an object.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = InstanceAdminPostCall(body=body, data_format=data_format)
        return await self._api.call(call, timeout=timeout)

    async def post_cluster_config(
        self,
        *,
        server_config: str | None = None,
        group: str | None = None,
        zone: str | None = None,
        cluster_config: bytes | None = None,
        timeout=UNSET,
    ) -> Response:
        """Exchange the configuration for a cluster join.

        Joining a host takes two requests: send the joining host's
        get_server_config output with its group to a host of the cluster, then
        send the returned ZIP archive as cluster_config to the joining host,
        which restarts. Include either server_config or cluster_config. Send the
        archive only to the joining host: MarkLogic Server 12.1 also accepts it
        on an initialized host and replaces that host's cluster configuration.

        Documentation: https://docs.marklogic.com/REST/POST/admin/v1/cluster-config

        Parameters
        ----------
        server_config : str | None
            The server configuration of a new host to be joined to this cluster.
            Its value should be the output of a previous call to
            GET /admin/v1/server-config. Sent as form data in the request body.
            You must include either this parameter or the cluster_config
            parameter, but not both.
        group : str | None
            The group of the new host. Required with the server_config parameter,
            not permitted otherwise.
        zone : str | None
            Optional text describing the location of the new host, such as the
            name of an Amazon EC2 Availability Zone. Used by the Tiered Storage
            API to configure local disk failover. Permitted only with the
            server_config parameter.
        cluster_config : bytes | None
            The cluster configuration in ZIP format, as returned by a previous
            request with the server_config parameter. Sent to the joining host
            to complete the cluster join. You must include either this parameter
            or the server_config parameter, but not both.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 200 with the cluster configuration ZIP archive
            for a server_config request, 202 with a restart timestamp for a
            cluster_config request

        Raises
        ------
        WrongParametersError
            If neither or both of server_config and cluster_config are given,
            server_config is given without group, or group or zone is given
            with cluster_config.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ClusterConfigPostCall(
            server_config=server_config,
            group=group,
            zone=zone,
            cluster_config=cluster_config,
        )
        return await self._api.call(call, timeout=timeout)

    async def delete_host_config(
        self,
        *,
        remote_host: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """Drop a host from the cluster.

        The host must have no forests and must not be a replication bootstrap
        or shared disk failover host. Without remote_host the receiving host
        removes itself and restarts uninitialized; with it, the receiving host
        drops the remote host, which is no longer a viable instance.

        Documentation: https://docs.marklogic.com/REST/DELETE/admin/v1/host-config

        Parameters
        ----------
        remote_host : str | None
            Request a host in a cluster to remove the host referenced by this
            parameter. To request a host to remove itself, omit this parameter.
            The hostname must be resolvable on the host that receives the
            request. The remote host can be in any group in the cluster.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response: 202 with a restart timestamp when a host
            removes itself, 204 when it removes a remote host

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = HostConfigDeleteCall(remote_host=remote_host)
        return await self._api.call(call, timeout=timeout)
