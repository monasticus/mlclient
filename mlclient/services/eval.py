"""High-level Eval service.

Provides parsed code evaluation on MarkLogic.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElemTree
from pathlib import Path

from mlclient.calls import EvalCall
from mlclient.clients.api_client import ApiClient
from mlclient.exceptions import (
    MarkLogicError,
    UnsupportedFileExtensionError,
    WrongParametersError,
)
from mlclient.ml_response_parser import MLResponseParser

LOCAL_NS = "http://www.w3.org/2005/xquery-local-functions"

_XQUERY_FILE_EXT = ("xq", "xql", "xqm", "xqu", "xquery", "xqy")
_JAVASCRIPT_FILE_EXT = ("js", "sjs")
_SUPPORTED_FILE_EXT = tuple(
    extension
    for extensions in [_XQUERY_FILE_EXT, _JAVASCRIPT_FILE_EXT]
    for extension in extensions
)


class EvalService:
    """High-level service for /v1/eval endpoint."""

    def __init__(self, rest: ApiClient):
        self._rest = rest

    def xquery(
        self,
        code: str,
        *,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        output_type: type | None = None,
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
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        Parsed evaluation result
        """
        return self._eval(
            xq=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
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
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        Parsed evaluation result
        """
        return self._eval(
            js=code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
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
        """Evaluate XQuery code. Alias for :meth:`xquery`."""
        return self.xquery(
            code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
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
        """Evaluate JavaScript code. Alias for :meth:`javascript`."""
        return self.javascript(
            code,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
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
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        Parsed evaluation result
        """
        return self._eval(
            file=path,
            variables=variables,
            database=database,
            txid=txid,
            output_type=output_type,
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
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        Parsed evaluation result

        Raises
        ------
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
        **kwargs,
    ):
        """Execute eval and return parsed result."""
        _validate_params(file, xq, js)
        call = _get_call(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            **kwargs,
        )
        resp = self._rest.call(call)
        parsed_resp = MLResponseParser.parse(resp, output_type=output_type)
        if not resp.is_success:
            raise MarkLogicError(parsed_resp)
        return parsed_resp


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


def _get_call(
    file: str | None,
    xq: str | None,
    js: str | None,
    variables: dict | None,
    database: str | None,
    txid: str | None,
    **kwargs,
) -> EvalCall:
    """Prepare an EvalCall instance."""
    params = {
        "xquery": xq,
        "javascript": js,
        "variables": _get_variables(variables, kwargs),
        "database": database,
        "txid": txid,
    }

    if file:
        if file.endswith(_XQUERY_FILE_EXT):
            lang = "xquery"
        elif file.endswith(_JAVASCRIPT_FILE_EXT):
            lang = "javascript"
        else:
            extensions = ", ".join(_SUPPORTED_FILE_EXT)
            msg = f"Unknown file extension! Supported extensions are: {extensions}"
            raise UnsupportedFileExtensionError(msg)

        params[lang] = Path(file).read_text()

    return EvalCall(**params)


def _get_variables(
    variables: dict | None,
    kwargs: dict,
) -> dict:
    """Combine variables with kwargs."""
    if variables:
        variables.update(kwargs)
        return variables
    return kwargs
