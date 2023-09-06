"""The ML Eval Client module.

It exports high-level classes to easily evaluate code in MarkLogic server:
    * EvalClient
        An MLResourceClient calling /v1/eval endpoint.
"""
from __future__ import annotations

import xml.etree.ElementTree as ElemTree

from mlclient.calls import EvalCall
from mlclient.clients import MLResourceClient, MLResponseParser


class EvalClient(MLResourceClient):
    """An MLResourceClient calling /v1/eval endpoint.

    It is a high-level class parsing MarkLogic response and extracting values from
    the server.
    """

    def eval(
            self,
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
            xq=xq,
            js=js,
            variables=variables,
            database=database,
            txid=txid,
            **kwargs)
        resp = self.call(call)
        return MLResponseParser.parse(resp)

    @staticmethod
    def _get_call(
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

        return EvalCall(**params)


