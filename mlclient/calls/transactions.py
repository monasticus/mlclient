"""The ML Transaction Api Calls module.

This module provides call classes for multi-statement transaction REST resources.

It exports 3 classes:
    * TransactionsPostCall
        A POST request to create a multi-statement transaction.
    * TransactionGetCall
        A GET request to get a transaction status.
    * TransactionPostCall
        A POST request to commit or roll back a transaction.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls.api_call import ApiCall


class TransactionsPostCall(ApiCall):
    """A POST request to create a multi-statement transaction.

    An ApiCall implementation representing a single POST request
    to the /v1/transactions endpoint.

    Create a multi-statement transaction. The resulting transaction id may be used
    in the txid request parameter of subsequent requests to force evaluation to take
    place in the context of the created transaction.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/transactions
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/transactions"

    _NAME_PARAM: str = "name"
    _TIME_LIMIT_PARAM: str = "timeLimit"
    _DATABASE_PARAM: str = "database"

    def __init__(
        self,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
    ):
        """Initialize TransactionsPostCall instance.

        Parameters
        ----------
        name : str
            A symbolic name for the transaction. Default: client-txn.
        time_limit : int
            The transaction time limit to apply to this transaction, in seconds.
            If the transaction is not committed or rolled back within this time limit,
            the transaction is automatically rolled back.
        database : str
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        """
        super().__init__(
            method=constants.METHOD_POST,
            content_type=constants.HEADER_PLAIN_TEXT,
        )
        self.add_param(self._NAME_PARAM, name)
        self.add_param(self._TIME_LIMIT_PARAM, time_limit)
        self.add_param(self._DATABASE_PARAM, database)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Transactions call.

        Returns
        -------
        str
            A Transactions call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)


class TransactionGetCall(ApiCall):
    """A GET request to get a transaction status.

    An ApiCall implementation representing a single GET request
    to the /v1/transactions/{txid} endpoint.

    Retrieve status information for the transaction whose id matches the txid given
    in the request URI.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/transactions/[txid]
    """

    _API_VERSION: int = 1

    _ENDPOINT_TEMPLATE: str = "/v{}/transactions/{}"

    _FORMAT_PARAM: str = "format"
    _DATABASE_PARAM: str = "database"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json"]

    def __init__(
        self,
        txid: str,
        data_format: str = "xml",
        database: str | None = None,
    ):
        """Initialize TransactionGetCall instance.

        Parameters
        ----------
        txid : str
            A transaction identifier, as returned by TransactionsPostCall.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        database : str
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._txid = txid
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._DATABASE_PARAM, database)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Transaction call.

        Returns
        -------
        str
            A Transaction call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._txid)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class TransactionPostCall(ApiCall):
    """A POST request to commit or roll back a transaction.

    An ApiCall implementation representing a single POST request
    to the /v1/transactions/{txid} endpoint.

    Commit or roll back the transaction whose id matches the txid given
    in the request URI.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/transactions/[txid]
    """

    _API_VERSION: int = 1

    _ENDPOINT_TEMPLATE: str = "/v{}/transactions/{}"

    _RESULT_PARAM: str = "result"
    _DATABASE_PARAM: str = "database"

    _SUPPORTED_RESULTS: ClassVar[list] = ["commit", "rollback"]

    def __init__(
        self,
        txid: str,
        result: str,
        database: str | None = None,
    ):
        """Initialize TransactionPostCall instance.

        Parameters
        ----------
        txid : str
            A transaction identifier, as returned by TransactionsPostCall.
        result : str
            The desired outcome of the transaction. Allowed values: commit, rollback.
        database : str
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        """
        self._validate_params(result)
        super().__init__(
            method=constants.METHOD_POST,
            content_type=constants.HEADER_PLAIN_TEXT,
        )
        self._txid = txid
        self.add_param(self._RESULT_PARAM, result)
        self.add_param(self._DATABASE_PARAM, database)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Transaction call.

        Returns
        -------
        str
            A Transaction call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._txid)

    @classmethod
    def _validate_params(
        cls,
        result: str,
    ):
        if result not in cls._SUPPORTED_RESULTS:
            joined_supported_results = ", ".join(cls._SUPPORTED_RESULTS)
            msg = f"The supported results are: {joined_supported_results}"
            raise exceptions.WrongParametersError(msg)
