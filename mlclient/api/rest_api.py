"""REST API group for /v1/* endpoints (RestApi / AsyncRestApi).

Requires a REST app server.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import ApiCall

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient

from .documents import AsyncDocumentsApi, DocumentsApi
from .eval import AsyncEvalApi, EvalApi


class RestApi:
    """REST API group for /v1/* endpoints (eval, documents).

    Requires a REST app server.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def call(self, call_: ApiCall) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self._api.call(call_)

    @cached_property
    def eval(self) -> EvalApi:
        """Return the eval API group."""
        return EvalApi(self._api)

    @cached_property
    def documents(self) -> DocumentsApi:
        """Return the documents API group."""
        return DocumentsApi(self._api)


class AsyncRestApi:
    """Async REST API group for /v1/* endpoints (eval, documents)."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def call(self, call_: ApiCall) -> Response:
        """Send a custom ApiCall."""
        return await self._api.call(call_)

    @cached_property
    def eval(self) -> AsyncEvalApi:
        """Return the eval API group."""
        return AsyncEvalApi(self._api)

    @cached_property
    def documents(self) -> AsyncDocumentsApi:
        """Return the documents API group."""
        return AsyncDocumentsApi(self._api)
