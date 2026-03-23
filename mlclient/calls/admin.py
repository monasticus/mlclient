"""The ML Admin API Calls module.

It exports 2 classes:
    * TimestampGetCall
        A GET request to verify that MarkLogic Server is up and accepting requests.
    * ServerConfigGetCall
        A GET request to retrieve server configuration for cluster join.
"""

from __future__ import annotations

from mlclient.calls.api_call import ApiCall


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
