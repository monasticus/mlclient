"""The ML Invoke Api Call module.

It exports 1 class:
    * InvokeCall
        A POST request to evaluate a module installed in MarkLogic Server.
"""

from __future__ import annotations

from json import dumps

from mlclient import _constants as constants
from mlclient import exceptions
from mlclient.calls.base import ApiCall


class InvokeCall(ApiCall):
    """A POST request to evaluate a module installed in MarkLogic Server.

    An ApiCall implementation representing a single request
    to the /v1/invoke endpoint.

    Evaluate an XQuery or server-side JavaScript module installed in
    MarkLogic Server.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/invoke
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/invoke"

    _MODULE_PARAM: str = "module"
    _VARS_PARAM: str = "vars"
    _DATABASE_PARAM: str = "database"
    _TXID_PARAM: str = "txid"

    def __init__(
        self,
        module: str,
        variables: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
    ):
        """Initialize InvokeCall instance.

        Parameters
        ----------
        module : str
            The path of the module to be evaluated. The path is resolved against
            the root of the App Server that is part of your REST API instance
            or to the Modules database or directory. The module filename suffix
            determines whether the module is treated as XQuery or JavaScript.
        variables
            External variables to pass to the module
        database
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        """
        self._validate_params(module)

        super().__init__(
            method=constants.METHOD_POST,
            accept=constants.HEADER_MULTIPART_MIXED,
            content_type=constants.HEADER_X_WWW_FORM_URLENCODED,
        )
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._TXID_PARAM, txid)
        self.body = self._build_body(module, variables)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Invoke call.

        Returns
        -------
        str
            An Invoke call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        module: str | None,
    ):
        """Reject a missing or blank module path.

        Parameters
        ----------
        module : str | None
            The path of the module to be evaluated.

        Raises
        ------
        WrongParametersError
            If the module path is None, empty or whitespace only.
        """
        if not module or not module.strip():
            msg = "You must include the module parameter!"
            raise exceptions.WrongParametersError(msg)

    @classmethod
    def _build_body(
        cls,
        module: str,
        variables: dict | None,
    ):
        """Build the x-www-form-urlencoded body of the request.

        Parameters
        ----------
        module : str
            The path of the module to be evaluated.
        variables : dict | None
            External variables to pass to the module; omitted when empty.

        Returns
        -------
        dict
            The module path and, when given, JSON-encoded variables.
        """
        body = {cls._MODULE_PARAM: module}
        if variables:
            body[cls._VARS_PARAM] = dumps(variables)
        return body
