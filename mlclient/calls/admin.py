"""The ML Admin API Calls module.

It exports 7 classes:
    * TimestampGetCall
        A GET request to verify that MarkLogic Server is up and accepting requests.
    * TimestampHeadCall
        A HEAD request to verify that MarkLogic Server is up and accepting requests.
    * ServerConfigGetCall
        A GET request to retrieve server configuration for cluster join.
    * InitPostCall
        A POST request to initialize MarkLogic Server.
    * InstanceAdminPostCall
        A POST request to install the admin user and initialize security.
    * ClusterConfigPostCall
        A POST request to exchange the configuration for a cluster join.
    * HostConfigDeleteCall
        A DELETE request to drop a host from the cluster.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import _constants as constants
from mlclient import _utils as utils
from mlclient import exceptions
from mlclient.calls import _utils as call_utils
from mlclient.calls.base import ApiCall


class TimestampGetCall(ApiCall):
    """A GET request to verify that MarkLogic Server is up and accepting requests.

    An ApiCall implementation representing a single GET request
    to the /admin/v1/timestamp endpoint.

    Verify that MarkLogic Server is up and accepting requests. If MarkLogic
    Server is available, this request returns response code 200 (OK) and the
    response body contains a plain text timestamp that can be used with the
    timestamp returned by asynchronous admin and manage requests to confirm that
    a restart occurred and has completed.

    This request must be directed to the Admin Interface on port 8001.

    Management REST API requests that cause a restart usually return a reference
    to this service in the response Location header and/or the data in the
    response body. You can use this reference to test whether the restart has
    successfully completed.

    To test for a restart, call GET /admin/v1/timestamp prior to the operation
    that can cause a restart, then call it again afterwards, and compare the two
    timestamps.

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/admin/v1/timestamp
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/timestamp"

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)


class TimestampHeadCall(ApiCall):
    """A HEAD request to verify that MarkLogic Server is up and accepting requests.

    An ApiCall implementation representing a single HEAD request
    to the /admin/v1/timestamp endpoint.

    Verify that MarkLogic Server is up and accepting requests. If MarkLogic
    Server is available, this request returns response code 200 (OK) without
    a response body.

    This request must be directed to the Admin Interface on port 8001.

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/HEAD/admin/v1/timestamp
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/timestamp"

    def __init__(self):
        """Initialize TimestampHeadCall instance."""
        super().__init__(method=constants.METHOD_HEAD)

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)


class ServerConfigGetCall(ApiCall):
    """A GET request to retrieve server configuration for cluster join.

    An ApiCall implementation representing a single GET request
    to the /admin/v1/server-config endpoint.

    Retrieve MarkLogic Server configuration information, suitable for use in
    joining a cluster. Upon success, MarkLogic Server returns status code
    200 (OK) and the response body contains the requested information,
    expressed as XML. If license key installation and basic initialization have
    not yet been done, the response payload will include a timestamp, but all
    other elements will be empty.

    This request must be directed to the Admin Interface on port 8001.

    This method is intended for use in the context of other REST Management API
    methods during cluster configuration, such as using the data returned by
    this request as input to a POST request to /admin/v1/cluster-config.

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/admin/v1/server-config
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/server-config"

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)


class InitPostCall(ApiCall):
    """A POST request to initialize MarkLogic Server.

    An ApiCall implementation representing a single POST request
    to the /admin/v1/init endpoint.

    Initializes MarkLogic Server. Optional parameters below. You can: install or
    update a license key, and install or update a license key for a previously
    initialized instance of MarkLogic Server.

    This request must be directed to the Admin Interface on port 8001.

    It must be the first call made in setting up a MarkLogic Server instance and
    causes a restart (202 Accepted). On an initialized instance it only updates
    the license information included, if any (204 No Content).

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/POST/admin/v1/init
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/init"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json"]

    def __init__(
        self,
        body: str | dict | None = None,
        data_format: str | None = None,
    ):
        """Initialize InitPostCall instance.

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
        """
        self._validate_params(data_format)
        if body is None:
            content_type = constants.HEADER_X_WWW_FORM_URLENCODED
        else:
            body, content_type = call_utils.request_body_with_content_type(
                body,
                "POST /admin/v1/init",
            )
        accept = None
        if data_format is not None:
            accept = utils.get_accept_header_for_format(data_format)
        super().__init__(
            method=constants.METHOD_POST,
            accept=accept,
            content_type=content_type,
            body=body,
        )
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        data_format: str | None,
    ):
        call_utils.validate_supported(
            data_format,
            cls._SUPPORTED_FORMATS,
            "formats",
        )


class InstanceAdminPostCall(ApiCall):
    """A POST request to install the admin user and initialize security.

    An ApiCall implementation representing a single POST request
    to the /admin/v1/instance-admin endpoint.

    Install the admin username and password, and initialize the security
    database and objects.

    This request must be directed to the Admin Interface on port 8001.

    Call POST /admin/v1/init first. Use it only on a standalone host or on the
    initial bootstrap host of a cluster; additional hosts join through
    POST /admin/v1/cluster-config instead. Success causes a restart
    (202 Accepted); initialization cannot be repeated.

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/POST/admin/v1/instance-admin
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/instance-admin"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json"]

    def __init__(
        self,
        body: str | dict,
        data_format: str | None = None,
    ):
        """Initialize InstanceAdminPostCall instance.

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
        """
        self._validate_params(data_format)
        body, content_type = call_utils.request_body_with_content_type(
            body,
            "POST /admin/v1/instance-admin",
        )
        accept = None
        if data_format is not None:
            accept = utils.get_accept_header_for_format(data_format)
        super().__init__(
            method=constants.METHOD_POST,
            accept=accept,
            content_type=content_type,
            body=body,
        )
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        data_format: str | None,
    ):
        call_utils.validate_supported(
            data_format,
            cls._SUPPORTED_FORMATS,
            "formats",
        )


class ClusterConfigPostCall(ApiCall):
    """A POST request to exchange the configuration for a cluster join.

    An ApiCall implementation representing a single POST request
    to the /admin/v1/cluster-config endpoint.

    Provide host or cluster configuration information suitable for adding a new
    host to an existing cluster.

    This request must be directed to the Admin Interface on port 8001.

    A cluster join takes two requests. Sent to a fully initialized host of the
    cluster with the joining host's server configuration (GET
    /admin/v1/server-config) and its group, the request returns the cluster
    configuration as a ZIP archive (200 OK). Sent to the joining host with that
    archive, it completes the join and restarts the host (202 Accepted).

    Send the archive only to the joining host: MarkLogic Server 12.1 also
    accepts it on a host that is already initialized and replaces that host's
    cluster configuration.

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/POST/admin/v1/cluster-config
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/cluster-config"

    _SERVER_CONFIG_PARAM: str = "server-config"
    _GROUP_PARAM: str = "group"
    _ZONE_PARAM: str = "zone"

    def __init__(
        self,
        server_config: str | None = None,
        group: str | None = None,
        zone: str | None = None,
        cluster_config: bytes | None = None,
    ):
        """Initialize ClusterConfigPostCall instance.

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
        """
        self._validate_params(server_config, group, zone, cluster_config)
        if cluster_config is not None:
            super().__init__(
                method=constants.METHOD_POST,
                content_type=constants.HEADER_ZIP,
                body=cluster_config,
            )
        else:
            super().__init__(
                method=constants.METHOD_POST,
                content_type=constants.HEADER_X_WWW_FORM_URLENCODED,
                body=self._build_form(server_config, group, zone),
            )

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        server_config: str | None,
        group: str | None,
        zone: str | None,
        cluster_config: bytes | None,
    ):
        if server_config is None and cluster_config is None:
            msg = (
                "You must include either the server_config "
                "or the cluster_config parameter!"
            )
            raise exceptions.WrongParametersError(msg)
        if server_config is not None and cluster_config is not None:
            msg = (
                "You cannot include both the server_config "
                "and the cluster_config parameter!"
            )
            raise exceptions.WrongParametersError(msg)
        if server_config is not None and group is None:
            msg = "The group parameter is required with the server_config parameter!"
            raise exceptions.WrongParametersError(msg)
        if cluster_config is not None and (group is not None or zone is not None):
            msg = (
                "The group and zone parameters are permitted "
                "only with the server_config parameter!"
            )
            raise exceptions.WrongParametersError(msg)

    @classmethod
    def _build_form(
        cls,
        server_config: str,
        group: str,
        zone: str | None,
    ) -> dict:
        """Return the form data requesting the cluster configuration.

        Parameters
        ----------
        server_config : str
            The joining host's server configuration.
        group : str
            The group of the joining host.
        zone : str | None
            The location of the joining host; omitted when None.

        Returns
        -------
        dict
            Form fields keyed by their MarkLogic names.
        """
        form = {cls._SERVER_CONFIG_PARAM: server_config, cls._GROUP_PARAM: group}
        if zone is not None:
            form[cls._ZONE_PARAM] = zone
        return form


class HostConfigDeleteCall(ApiCall):
    """A DELETE request to drop a host from the cluster.

    An ApiCall implementation representing a single DELETE request
    to the /admin/v1/host-config endpoint.

    Remove a host's configuration from the cluster configuration, dropping the
    host from the cluster. The remote-host parameter is required if you are
    removing a host from a different group.

    This request must be directed to the Admin Interface on port 8001.

    The host must not have any forests, must not be a bootstrap host for
    database replication and must not be a failover host for shared disk
    failover; otherwise the request fails with 400. A host asked to remove
    itself restarts as a clean, uninitialized standalone host (202 Accepted).
    A host removed by another host (remote-host) is no longer a viable instance
    (204 No Content).

    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/DELETE/admin/v1/host-config
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/host-config"

    _REMOTE_HOST_PARAM: str = "remote-host"

    def __init__(
        self,
        remote_host: str | None = None,
    ):
        """Initialize HostConfigDeleteCall instance.

        Parameters
        ----------
        remote_host : str | None
            Request a host in a cluster to remove the host referenced by this
            parameter. To request a host to remove itself, omit this parameter.
            The hostname must be resolvable on the host that receives the
            request. The remote host can be in any group in the cluster.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self.add_param(self._REMOTE_HOST_PARAM, remote_host)

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)
