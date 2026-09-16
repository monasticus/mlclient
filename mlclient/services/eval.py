"""Higher-level Eval service (EvalService / AsyncEvalService).

Provides parsed code evaluation on MarkLogic.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElemTree
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from mlclient._options import UNSET

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi

from mlclient.exceptions import UnsupportedFileExtensionError, WrongParametersError
from mlclient.functions.xqy._expr import Expr
from mlclient.responses import MLResponseParser

_LOCAL_NS = "http://www.w3.org/2005/xquery-local-functions"

_XQUERY_FILE_EXT = ("xq", "xql", "xqm", "xqu", "xquery", "xqy")
_JAVASCRIPT_FILE_EXT = ("js", "sjs")
_SUPPORTED_FILE_EXT = tuple(
    extension
    for extensions in [_XQUERY_FILE_EXT, _JAVASCRIPT_FILE_EXT]
    for extension in extensions
)


class EvalService:
    """Higher-level service for /v1/eval endpoint."""

    def __init__(self, rest: RestApi):
        self._rest = rest

    def expression(
        self,
        expr: Expr,
        *,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
    ) -> list:
        """Compile and execute an expression as the root of one eval request.

        Parameters
        ----------
        expr : Expr
            A builder expression, including nested calls or a positional window.
        database : str | None, default None
            Content database name or id.
        txid : str | None, default None
            Existing multi-statement transaction identifier.
        output_type : type | None, default None
            Per-item raw conversion (``str`` or ``bytes``), or typed conversion.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout; unset inherits the client configuration.

        Returns
        -------
        list
            Zero, one or many result items. Decimal results are ``Decimal``;
            date/time results use Python types. A JSON array stays a single item.

        Raises
        ------
        TypeError
            If the root is not an expression or an unknown keyword is supplied.
        ValueError
            If output_type is not None, str or bytes.
        MarkLogicError
            If the server rejects the expression, including unavailable functions.
        """
        if not isinstance(expr, Expr):
            message = "expression requires an Expr"
            raise TypeError(message)
        if output_type not in (None, str, bytes):
            message = "output_type must be None, str or bytes"
            raise ValueError(message)
        code, variables = expr.compile()
        response = self._rest.eval.post(
            xquery=code,
            variables=variables,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        if not response.is_success:
            raise MarkLogicError(MLResponseParser.parse(response))
        return MLResponseParser.parse_sequence(response, output_type)

    def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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

    def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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

    def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self.xquery(
            code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return self.javascript(
            code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate code from a file in MarkLogic (auto-detect language).

        Parameters
        ----------
        path : str
            File path to the code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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

    def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ):
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
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ):
        """Execute eval and return parsed result."""
        _validate_params(file, xq, js)
        params = _get_eval_params(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            **kwargs,
        )
        resp = self._rest.eval.post(**params, timeout=timeout)
        MLResponseParser.raise_for_status(resp)
        return MLResponseParser.parse(resp, output_type=output_type)


def _validate_params(
    file: str | None,
    xq: str | None,
    js: str | None,
):
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
    **kwargs,
) -> dict:
    """Prepare keyword arguments for EvalApi.post."""
    params = {
        "xquery": xq,
        "javascript": js,
        "variables": _get_variables(variables, kwargs),
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
    **kwargs,
) -> dict:
    """Prepare keyword arguments for AsyncEvalApi.post, reading files asynchronously."""
    params = {
        "xquery": xq,
        "javascript": js,
        "variables": _get_variables(variables, kwargs),
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
    extensions = ", ".join(_SUPPORTED_FILE_EXT)
    msg = f"Unknown file extension! Supported extensions are: {extensions}"
    raise UnsupportedFileExtensionError(msg)


def _get_variables(
    variables: dict | None,
    kwargs: dict,
) -> dict:
    """Combine variables with kwargs."""
    if variables:
        variables.update(kwargs)
        return variables
    return kwargs


class AsyncEvalService:
    """Async higher-level service for /v1/eval endpoint."""

    def __init__(self, rest: AsyncRestApi):
        self._rest = rest

    async def expression(
        self,
        expr: Expr,
        *,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
    ) -> list:
        """Compile and execute an expression as the root of one eval request.

        Parameters
        ----------
        expr : Expr
            A builder expression, including nested calls or a positional window.
        database : str | None, default None
            Content database name or id.
        txid : str | None, default None
            Existing multi-statement transaction identifier.
        output_type : type | None, default None
            Per-item raw conversion (``str`` or ``bytes``), or typed conversion.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout; unset inherits the client configuration.

        Returns
        -------
        list
            Zero, one or many result items. Decimal results are ``Decimal``;
            date/time results use Python types. A JSON array stays a single item.

        Raises
        ------
        TypeError
            If the root is not an expression or an unknown keyword is supplied.
        ValueError
            If output_type is not None, str or bytes.
        MarkLogicError
            If the server rejects the expression, including unavailable functions.
        """
        if not isinstance(expr, Expr):
            message = "expression requires an Expr"
            raise TypeError(message)
        if output_type not in (None, str, bytes):
            message = "output_type must be None, str or bytes"
            raise ValueError(message)
        code, variables = expr.compile()
        response = await self._rest.eval.post(
            xquery=code,
            variables=variables,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        if not response.is_success:
            raise MarkLogicError(MLResponseParser.parse(response))
        return MLResponseParser.parse_sequence(response, output_type)

    async def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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

    async def javascript(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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

    async def xqy(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate XQuery code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw XQuery code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self.xquery(
            code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    async def js(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate JavaScript code in MarkLogic.

        Parameters
        ----------
        code : str
            Raw JavaScript code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        return await self.javascript(
            code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
            timeout=timeout,
            **kwargs,
        )

    async def file(
        self,
        path: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ) -> (
        bytes
        | str
        | int
        | float
        | bool
        | dict
        | ElemTree.ElementTree
        | ElemTree.Element
        | list
    ):
        """Evaluate code from a file in MarkLogic (auto-detect language).

        Parameters
        ----------
        path : str
            File path to the code to evaluate
        variables : dict | None, default None
            External variables
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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

    async def execute(
        self,
        *,
        file: str | None = None,
        xq: str | None = None,
        js: str | None = None,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ):
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
        database : str | None, default None
            Content database name or id
        txid : str | None, default None
            Transaction identifier
        output_type : type | None, default None
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
        Parsed evaluation result

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
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
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
        timeout=UNSET,
        **kwargs,
    ):
        """Execute eval and return parsed result."""
        _validate_params(file, xq, js)
        params = await _async_get_eval_params(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            **kwargs,
        )
        resp = await self._rest.eval.post(**params, timeout=timeout)
        MLResponseParser.raise_for_status(resp)
        return MLResponseParser.parse(resp, output_type=output_type)
