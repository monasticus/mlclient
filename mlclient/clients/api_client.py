"""The API Client module (ApiClient / AsyncApiClient).

Exports sync and async mid-level clients for calling MarkLogic API endpoints
via ApiCall objects.
"""

from __future__ import annotations

from httpx import Response

from mlclient.calls import ApiCall
from mlclient.connection import UNSET

from .http_client import AsyncHttpClient, HttpClient


class ApiClient:
    """Mid-level client providing call() for ApiCall objects."""

    def __init__(self, http: HttpClient):
        self._http = http

    def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a request using an ApiCall object.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout applied to this call only. Unset uses the
            client's configured timeout. None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It is an execution option, never sent
            as a request parameter, header or body.

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
            timeout=timeout,
        )


class AsyncApiClient:
    """Async mid-level client providing call() for ApiCall objects."""

    def __init__(self, http: AsyncHttpClient):
        self._http = http

    async def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a request using an ApiCall object.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout applied to this call only. Unset uses the
            client's configured timeout. None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It is an execution option, never sent
            as a request parameter, header or body.

        Returns
        -------
        Response
            An HTTP response
        """
        return await self._http.request(
            method=call_.method,
            endpoint=call_.endpoint,
            params=call_.params,
            headers=call_.headers,
            body=call_.body,
            timeout=timeout,
        )
