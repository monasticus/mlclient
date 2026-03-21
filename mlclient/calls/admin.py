"""The ML Admin API Calls module.

It exports 2 classes:
    * TimestampGetCall
        A GET request to get the Admin server timestamp.
    * ServerConfigGetCall
        A GET request to get the Admin server configuration.
"""

from __future__ import annotations

from mlclient.calls.api_call import ApiCall


class TimestampGetCall(ApiCall):
    """A GET request to get the Admin server timestamp.

    An ApiCall implementation representing a single GET request
    to the /admin/v1/timestamp endpoint.
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/timestamp"

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)


class ServerConfigGetCall(ApiCall):
    """A GET request to get the Admin server configuration.

    An ApiCall implementation representing a single GET request
    to the /admin/v1/server-config endpoint.
    """

    _API_VERSION: int = 1
    _ENDPOINT: str = "/admin/v{}/server-config"

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return self._ENDPOINT.format(self._API_VERSION)
