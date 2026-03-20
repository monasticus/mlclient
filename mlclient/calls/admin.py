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

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return "/admin/v1/timestamp"


class ServerConfigGetCall(ApiCall):
    """A GET request to get the Admin server configuration.

    An ApiCall implementation representing a single GET request
    to the /admin/v1/server-config endpoint.
    """

    @property
    def endpoint(self) -> str:
        """Return the endpoint."""
        return "/admin/v1/server-config"
