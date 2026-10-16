"""Higher-level Invoke service (InvokeService / AsyncInvokeService).

Provides parsed evaluation of modules installed in MarkLogic.
"""

from __future__ import annotations

from mlclient._options import UNSET
from mlclient.models.results import ParsedValue
from mlclient.services._execution import ExecutionService


class InvokeService(ExecutionService):
    """Higher-level service for /v1/invoke endpoint.

    Invokes XQuery or server-side JavaScript modules installed in MarkLogic.
    A module path resolves against the modules database or directory of the
    App Server receiving the request. Invoking requires the xdmp-invoke
    privilege, not xdmp-eval.
    """

    def module(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> ParsedValue:
        """Invoke a module installed in MarkLogic and parse its result.

        Parameters
        ----------
        path : str
            The module path, such as ``/ext/report.xqy``, resolved against the
            App Server's modules database or directory. Its suffix selects
            XQuery or JavaScript.
        variables : dict | None, default None
            External variables; the dictionary is not modified.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this invocation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a module variable - to pass a module variable
            literally named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables; they override explicit
            variables of the same name.

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        WrongParametersError
            If the module path is missing or blank.
        MarkLogicError
            If MarkLogic returns an error, including a module that does not exist.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        response = self._rest.invoke.post(
            path,
            variables=self._merge_variables(variables, kwargs),
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, output_type)


class AsyncInvokeService(ExecutionService):
    """Async higher-level service for /v1/invoke endpoint.

    Invokes XQuery or server-side JavaScript modules installed in MarkLogic.
    A module path resolves against the modules database or directory of the
    App Server receiving the request. Invoking requires the xdmp-invoke
    privilege, not xdmp-eval.
    """

    async def module(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> ParsedValue:
        """Invoke a module installed in MarkLogic and parse its result.

        Parameters
        ----------
        path : str
            The module path, such as ``/ext/report.xqy``, resolved against the
            App Server's modules database or directory. Its suffix selects
            XQuery or JavaScript.
        variables : dict | None, default None
            External variables; the dictionary is not modified.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this invocation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a module variable - to pass a module variable
            literally named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables; they override explicit
            variables of the same name.

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        WrongParametersError
            If the module path is missing or blank.
        MarkLogicError
            If MarkLogic returns an error, including a module that does not exist.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        response = await self._rest.invoke.post(
            path,
            variables=self._merge_variables(variables, kwargs),
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, output_type)
