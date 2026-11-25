"""Higher-level Eval service (EvalService / AsyncEvalService).

Provides parsed code evaluation on MarkLogic.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, overload

import aiofiles

from mlclient._options import UNSET, UnsetType
from mlclient.exceptions import UnsupportedFileExtensionError, WrongParametersError
from mlclient.models.results import ParsedValue
from mlclient.services._execution import ExecutionService
from mlclient.xquery.expressions import XqyExpression

if TYPE_CHECKING:
    import httpx

_XQUERY_FILE_EXT = ("xq", "xql", "xqm", "xqu", "xquery", "xqy")
_JAVASCRIPT_FILE_EXT = ("js", "sjs")
SUPPORTED_FILE_EXTENSIONS = tuple(
    extension
    for extensions in [_XQUERY_FILE_EXT, _JAVASCRIPT_FILE_EXT]
    for extension in extensions
)


class EvalService(ExecutionService):
    """Higher-level service for /v1/eval endpoint."""

    @overload
    def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> ParsedValue: ...

    @overload
    def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> str | list[str]: ...

    @overload
    def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> bytes | list[bytes]: ...

    def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> ParsedValue:
        """Compile and execute an expression as the root of one eval request.

        Parameters
        ----------
        expr : XqyExpression
            A builder expression, including nested calls or a positional range.
        namespaces : dict[str, str] | None
            Prefix-to-URI bindings for this invocation only.
            They become XQuery namespace declarations,
            shared by validation and execution. The empty prefix sets the default
            element namespace.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            Per-item raw conversion (``str`` or ``bytes``), or typed conversion.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout; unset inherits the client configuration.

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list. Decimal results retain precision. A singleton
            JSON array returns that array without an extra outer list.

        Raises
        ------
        TypeError
            If the root is not an expression or an unknown keyword is supplied.
        ValueError
            If output_type is not None, str or bytes.
        MarkLogicError
            If the server rejects the expression, including unavailable functions.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        """
        if not isinstance(expr, XqyExpression):
            message = "expression requires an XqyExpression"
            raise TypeError(message)
        if output_type not in (None, str, bytes):
            message = "output_type must be None, str or bytes"
            raise ValueError(message)
        code, variables = expr.compile(namespaces=namespaces)
        response = self._rest.eval.post(
            xquery=code,
            variables=variables,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, output_type)

    @overload
    def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return self._eval(
            xq=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return self._eval(
            js=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return self._eval(
            xq=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return self._eval(
            js=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate code from a file in MarkLogic (auto-detect language).

        Parameters
        ----------
        path : str
            File path to the code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return self._eval(
            file=path,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate code in a MarkLogic server (general-purpose).

        Dynamically resolves the code type from the provided parameters.
        For explicit, typed calls prefer xquery(), javascript(), or file().

        Parameters
        ----------
        file : str | None, default None
            A file path of a code to evaluate
        xq : str | None, default None
            A raw XQuery code to evaluate
        js : str | None, default None
            A raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables to pass to the query during evaluation
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        MarkLogicError
            If MarkLogic returns an error
        """
        return self._eval(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    def _eval(
        self,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Execute eval and return parsed result."""
        _validate_params(file, xq, js)
        params = _get_eval_params(
            file=file,
            xq=xq,
            js=js,
            variables=self._merge_variables(variables, kwargs),
            **self._request_scope(database, txid),
        )
        resp = self._rest.eval.post(**params, timeout=timeout)
        return self._parse_result(resp, output_type)


def _validate_params(
    file: str | None,
    xq: str | None,
    js: str | None,
) -> None:
    """Validate parameters."""
    if file and xq:
        msg = "You cannot include both the file and the xquery parameter!"
        raise WrongParametersError(msg)
    if file and js:
        msg = "You cannot include both the file and the javascript parameter!"
        raise WrongParametersError(msg)


def _get_eval_params(
    file: str | None,
    xq: str | None,
    js: str | None,
    variables: dict | None,
    database: str | None,
    txid: str | None,
) -> dict:
    """Prepare keyword arguments for EvalApi.post."""
    params = {
        "xquery": xq,
        "javascript": js,
        "variables": variables,
        "database": database,
        "txid": txid,
    }

    if file:
        lang = _file_language(file)
        params[lang] = Path(file).read_text()

    return params


async def _async_get_eval_params(
    file: str | None,
    xq: str | None,
    js: str | None,
    variables: dict | None,
    database: str | None,
    txid: str | None,
) -> dict:
    """Prepare keyword arguments for AsyncEvalApi.post, reading files asynchronously."""
    params = {
        "xquery": xq,
        "javascript": js,
        "variables": variables,
        "database": database,
        "txid": txid,
    }

    if file:
        lang = _file_language(file)
        async with aiofiles.open(file) as f:
            params[lang] = await f.read()

    return params


def _file_language(file: str) -> str:
    """Resolve xquery/javascript from a code file's extension."""
    if file.endswith(_XQUERY_FILE_EXT):
        return "xquery"
    if file.endswith(_JAVASCRIPT_FILE_EXT):
        return "javascript"
    extensions = ", ".join(SUPPORTED_FILE_EXTENSIONS)
    msg = f"Unknown file extension! Supported extensions are: {extensions}"
    raise UnsupportedFileExtensionError(msg)


class AsyncEvalService(ExecutionService):
    """Async higher-level service for /v1/eval endpoint."""

    @overload
    async def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> ParsedValue: ...

    @overload
    async def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> str | list[str]: ...

    @overload
    async def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> bytes | list[bytes]: ...

    async def expression(
        self,
        expr: XqyExpression,
        *,
        namespaces: dict[str, str] | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
    ) -> ParsedValue:
        """Compile and execute an expression as the root of one eval request.

        Parameters
        ----------
        expr : XqyExpression
            A builder expression, including nested calls or a positional range.
        namespaces : dict[str, str] | None
            Prefix-to-URI bindings for this invocation only.
            They become XQuery namespace declarations,
            shared by validation and execution. The empty prefix sets the default
            element namespace.
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            Per-item raw conversion (``str`` or ``bytes``), or typed conversion.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout; unset inherits the client configuration.

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list. Decimal results retain precision. A singleton
            JSON array returns that array without an extra outer list.

        Raises
        ------
        TypeError
            If the root is not an expression or an unknown keyword is supplied.
        ValueError
            If output_type is not None, str or bytes.
        MarkLogicError
            If the server rejects the expression, including unavailable functions.
        httpx.HTTPStatusError
            If an HTTP failure has no recognized MarkLogic error payload.
        """
        if not isinstance(expr, XqyExpression):
            message = "expression requires an XqyExpression"
            raise TypeError(message)
        if output_type not in (None, str, bytes):
            message = "output_type must be None, str or bytes"
            raise ValueError(message)
        code, variables = expr.compile(namespaces=namespaces)
        response = await self._rest.eval.post(
            xquery=code,
            variables=variables,
            **self._request_scope(database, txid),
            timeout=timeout,
        )
        return self._parse_result(response, output_type)

    @overload
    async def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    async def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    async def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    async def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return await self._eval(
            xq=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    async def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    async def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    async def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    async def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return await self._eval(
            js=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    async def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    async def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    async def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    async def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return await self._eval(
            xq=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    async def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    async def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    async def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    async def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return await self._eval(
            js=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    async def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    async def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    async def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    async def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate code from a file in MarkLogic (auto-detect language).

        Parameters
        ----------
        path : str
            File path to the code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        """
        return await self._eval(
            file=path,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    @overload
    async def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue: ...

    @overload
    async def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> str | list[str]: ...

    @overload
    async def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[bytes],
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> bytes | list[bytes]: ...

    async def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Evaluate code in a MarkLogic server (general-purpose).

        Dynamically resolves the code type from the provided parameters.
        For explicit, typed calls prefer xquery(), javascript(), or file().

        Parameters
        ----------
        file : str | None, default None
            A file path of a code to evaluate
        xq : str | None, default None
            A raw XQuery code to evaluate
        js : str | None, default None
            A raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables to pass to the query during evaluation
        database : str | None, default unset
            Content database name or id; unset inherits the service scope and
            None clears it.
        txid : str | None, default unset
            Transaction identifier; unset inherits the service scope and
            None clears it.
        output_type : type[str | bytes] | None, default None
            A raw output type (supported: str, bytes)
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this evaluation. Unset uses the
            client's configured timeout; None disables every HTTP timeout; a
            number sets all four components to that many seconds; an
            httpx.Timeout overrides them. It bounds the HTTP request only and is
            never sent as a query variable - to pass a query variable literally
            named "timeout" use variables={"timeout": ...}.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        ParsedValue
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires on the last
            attempt the retry policy allows. The default policy does not retry
            read timeouts.
        MarkLogicError
            If MarkLogic returns an error
        """
        return await self._eval(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    async def _eval(
        self,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | UnsetType | None = UNSET,
        txid: str | UnsetType | None = UNSET,
        output_type: type[str | bytes] | None = None,
        timeout: httpx.Timeout | float | UnsetType | None = UNSET,
        **kwargs: object,
    ) -> ParsedValue:
        """Execute eval and return parsed result."""
        _validate_params(file, xq, js)
        params = await _async_get_eval_params(
            file=file,
            xq=xq,
            js=js,
            variables=self._merge_variables(variables, kwargs),
            **self._request_scope(database, txid),
        )
        resp = await self._rest.eval.post(**params, timeout=timeout)
        return self._parse_result(resp, output_type)
