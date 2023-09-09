"""The ML Eval Client module.

It exports high-level classes to easily evaluate code in MarkLogic server:
    * EvalClient
        An MLResourceClient calling /v1/eval endpoint.
"""
from __future__ import annotations

import xml.etree.ElementTree as ElemTree
from pathlib import Path

from mlclient.calls import EvalCall
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.exceptions import (MarkLogicError, UnsupportedFileExtensionError,
                                 WrongParametersError)

LOCAL_NS = "http://www.w3.org/2005/xquery-local-functions"


class EvalClient(MLResourceClient):
    """An MLResourceClient calling /v1/eval endpoint.

    It is a high-level class parsing MarkLogic response and extracting values from
    the server.
    """

    _XQUERY_FILE_EXT = ("xq", "xql", "xqm", "xqu", "xquery", "xqy")
    _JAVASCRIPT_FILE_EXT = ("js", "sjs")
    _SUPPORTED_FILE_EXT = (
        extension
        for extensions in [_XQUERY_FILE_EXT, _JAVASCRIPT_FILE_EXT]
        for extension in extensions)

    def eval(
            self,
            file: str | None = None,
            xq: str | None = None,
            js: str | None = None,
            variables: dict | None = None,
            database: str | None = None,
            txid: str | None = None,
            raw: bool = False,
            **kwargs,
    ) -> (bytes | str | int | float | bool | dict |
          ElemTree.ElementTree | ElemTree.Element |
          list):
        """Evaluate code in a MarkLogic server and get results.

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
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None, default None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        raw : bool, default False
            If True, body parts are parsed to string
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        bytes | str | int | float | bool | dict |
        ElemTree.ElementTree | ElemTree.Element |
        list
            A code evaluation result

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        self._validate_params(file, xq, js)
        call = self._get_call(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            **kwargs)
        resp = self.call(call)
        parsed_resp = MLResponseParser.parse(resp, raw=raw)
        if not resp.ok:
            raise MarkLogicError(parsed_resp)
        return parsed_resp

    @classmethod
    def _get_call(
            cls,
            file: str | None,
            xq: str | None,
            js: str | None,
            variables: dict | None,
            database: str | None,
            txid: str | None,
            **kwargs,
    ) -> EvalCall:
        """Prepare an EvalCall instance.

        It initializes an EvalCall instance with adjusted parameters. It combines
        variables with kwargs. It also uses a file content if provided to use as
        xquery / javascript value.

        Parameters
        ----------
        file : str | None
            A file path of a code to evaluate
        xq : str | None
            A raw XQuery code to evaluate
        js : str | None
            A raw JavaScript code to evaluate
        variables : dict | None
            External variables to pass to the query during evaluation
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        EvalCall
            A prepared EvalCall instance

        Raises
        ------
        UnsupportedFileExtensionError
            If the file path provided includes unsupported extension.
        WrongParametersError
            If the xquery and javascript were not provided or provided both
        """
        params = {
            "xquery": xq,
            "javascript": js,
            "variables": cls._get_variables(variables, kwargs),
            "database": database,
            "txid": txid,
        }

        if file:
            if file.endswith(cls._XQUERY_FILE_EXT):
                lang = "xquery"
            elif file.endswith(cls._JAVASCRIPT_FILE_EXT):
                lang = "javascript"
            else:
                extensions = ", ".join(cls._SUPPORTED_FILE_EXT)
                msg = f"Unknown file extension! Supported extensions are: {extensions}"
                raise UnsupportedFileExtensionError(msg)

            params[lang] = Path(file).read_text()

        return EvalCall(**params)

    @staticmethod
    def _get_variables(
            variables: dict | None,
            kwargs: dict,
    ) -> dict:
        """Combine variables with kwargs.

        Parameters
        ----------
        variables : dict | None
            External variables to pass to the query during evaluation
        kwargs : dict
            Key value arguments used as variables

        Returns
        -------
        dict
            External variables to pass to the query during evaluation
        """
        if variables:
            variables.update(kwargs)
            return variables
        return kwargs

    @staticmethod
    def _validate_params(
            file: str | None,
            xq: str | None,
            js: str | None,
    ):
        """Validate parameters.

        Parameters
        ----------
        file : str | None
            A file path of a code to evaluate
        xq : str | None
            A raw XQuery code to evaluate
        js : str | None
            A raw JavaScript code to evaluate

        Raises
        ------
        WrongParametersError
            If the file parameter has been provided together with xq or js
        """
        if file and xq:
            msg = "You cannot include both the file and the xquery parameter!"
            raise WrongParametersError(msg)
        if file and js:
            msg = "You cannot include both the file and the javascript parameter!"
            raise WrongParametersError(msg)

