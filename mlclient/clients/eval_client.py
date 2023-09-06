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

LOCAL_NS = "http://www.w3.org/2005/xquery-local-functions"


class EvalClient(MLResourceClient):
    """An MLResourceClient calling /v1/eval endpoint.

    It is a high-level class parsing MarkLogic response and extracting values from
    the server.
    """

    _XQUERY_FILE_EXT = ("xq", "xql", "xqm", "xqu", "xquery", "xqy")
    _JAVASCRIPT_FILE_EXT = ("js", "sjs")

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
        call = self._get_call(
            file=file,
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            **kwargs)
        resp = self.call(call)
        return MLResponseParser.parse(resp)

    @classmethod
    def _get_call(
            cls,
            file: str | None = None,
            xq: str | None = None,
            js: str | None = None,
            variables: dict | None = None,
            database: str | None = None,
            txid: str | None = None,
            **kwargs,
    ) -> EvalCall:
        if variables:
            variables.update(kwargs)
        else:
            variables = kwargs
        params = {
            "xquery": xq,
            "javascript": js,
            "variables": variables,
            "database": database,
            "txid": txid,
        }

        if file:
            if file.endswith(cls._XQUERY_FILE_EXT):
                lang = "xquery"
            elif file.endswith(cls._JAVASCRIPT_FILE_EXT):
                lang = "javascript"

            params[lang] = Path(file).read_text()

        return EvalCall(**params)


