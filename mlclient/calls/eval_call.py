"""The ML Eval Resource Call module.

It exports 1 class:
    * EvalCall
        A POST request to evaluate an ad-hoc query.
"""
from __future__ import annotations

from json import dumps

from mlclient import constants, exceptions
from mlclient.calls import ResourceCall


class EvalCall(ResourceCall):
    """A POST request to evaluate an ad-hoc query.

    A ResourceCall implementation representing a single request
    to the /v1/eval REST Resource.

    Evaluate an ad-hoc query expressed using XQuery or server-side JavaScript.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/eval
    """

    _ENDPOINT: str = "/v1/eval"

    _XQ_PARAM: str = "xquery"
    _JS_PARAM: str = "javascript"
    _VARS_PARAM: str = "vars"
    _DATABASE_PARAM: str = "database"
    _TXID_PARAM: str = "txid"

    def __init__(
            self,
            xquery: str | None = None,
            javascript: str | None = None,
            variables: dict | None = None,
            database: str | None = None,
            txid: str | None = None,
    ):
        """Initialize EvalCall instance.

        Parameters
        ----------
        xquery : str
            The query to evaluate, expressed using XQuery.
            You must include either this parameter or the javascript parameter,
            but not both.
        javascript : str
            The query to evaluate, expressed using server-side JavaScript.
            You must include either this parameter or the xquery parameter,
            but not both.
        variables
            External variables to pass to the query during evaluation
        database
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        """
        self._validate_params(xquery, javascript)

        super().__init__(method=constants.METHOD_POST,
                         accept=constants.HEADER_MULTIPART_MIXED,
                         content_type=constants.HEADER_X_WWW_FORM_URLENCODED)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._TXID_PARAM, txid)
        self.body = self._build_body(xquery, javascript, variables)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Eval call.

        Returns
        -------
        str
            An Eval call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            xquery: str,
            javascript: str,
    ):
        if not xquery and not javascript:
            msg = "You must include either the xquery or the javascript parameter!"
            raise exceptions.WrongParametersError(msg)
        if xquery and javascript:
            msg = "You cannot include both the xquery and the javascript parameter!"
            raise exceptions.WrongParametersError(msg)

    @classmethod
    def _build_body(
            cls,
            xquery: str,
            javascript: str,
            variables: dict,
    ):
        code_lang = cls._XQ_PARAM if xquery else cls._JS_PARAM
        code_to_eval = cls._normalize_code(xquery if xquery else javascript)
        body = {code_lang: code_to_eval}
        if variables:
            body[cls._VARS_PARAM] = dumps(variables)
        return body

    @staticmethod
    def _normalize_code(
            code: str,
    ):
        one_line_code = code.replace("\n", " ")
        return " ".join(one_line_code.split())
