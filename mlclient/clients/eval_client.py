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
            **kwargs,
    ) -> (bytes | str | int | float | bool | dict |
          ElemTree.ElementTree | ElemTree.Element |
          list):
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
        parsed_resp = MLResponseParser.parse(resp)
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
        if file and xq:
            msg = "You cannot include both the file and the xquery parameter!"
            raise WrongParametersError(msg)
        if file and js:
            msg = "You cannot include both the file and the javascript parameter!"
            raise WrongParametersError(msg)

