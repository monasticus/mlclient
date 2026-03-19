"""The REST Client module.

It exports the RestClient class for calling MarkLogic REST endpoints
via RestCall objects.
"""

from __future__ import annotations

from httpx import Response

from mlclient.calls import RestCall

from .http_client import HttpClient


class RestClient:
    """Mid-level client providing call() for RestCall objects.

    Attributes
    ----------
    http : HttpClient
        The underlying HTTP client used for requests.
    """

    def __init__(self, http: HttpClient):
        self._http = http

    @property
    def http(self) -> HttpClient:
        """Return the underlying HTTP client."""
        return self._http

    def call(self, call_: RestCall) -> Response:
        """Send a request using a RestCall object.

        Parameters
        ----------
        call_ : RestCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self._http.request(
            method=call_.method,
            endpoint=call_.endpoint,
            params=call_.params,
            headers=call_.headers,
            body=call_.body,
        )
