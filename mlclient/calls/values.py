"""The ML Values Api Calls module.

It exports 3 classes:
    * ValuesGetCall
        A GET request to list lexicon configurations of query options.
    * ValueGetCall
        A GET request to query the values in a lexicon or range index.
    * ValuePostCall
        A POST request to query lexicon values with a query in the request body.
"""

from __future__ import annotations

from typing import ClassVar
from urllib.parse import quote

from mlclient import _constants as constants, _utils as utils, exceptions
from mlclient.calls.base import ApiCall


class ValuesGetCall(ApiCall):
    """A GET request to list lexicon configurations of query options.

    An ApiCall implementation representing a single GET request
    to the /v1/values endpoint.

    Retrieve a list of lexicon configurations available for use with
    GET /v1/values/{name}.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/values
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/values"

    _DATABASE_PARAM: str = "database"
    _FORMAT_PARAM: str = "format"
    _OPTIONS_PARAM: str = "options"

    _SUPPORTED_FORMATS: ClassVar[list] = ["json", "xml"]

    def __init__(
        self,
        database: str | None = None,
        data_format: str = "xml",
        options: str | None = None,
    ):
        """Initialize ValuesGetCall instance.

        Parameters
        ----------
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        options : str
            The query options for which to list available lexicon configurations.
        """
        utils.validate_supported(
            data_format,
            self._SUPPORTED_FORMATS,
            "formats",
            required=True,
        )
        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._params = {
            name: value
            for name, value in {
                self._DATABASE_PARAM: database,
                self._FORMAT_PARAM: data_format,
                self._OPTIONS_PARAM: options,
            }.items()
            if value is not None
        }

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Values call.

        Returns
        -------
        str
            A Values call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)


class _ValueCall(ApiCall):
    """Query parameters, validation and endpoint shared by /v1/values/{name}."""

    _API_VERSION: int = 1

    _ENDPOINT_TEMPLATE: str = "/v{}/values/{}"

    _Q_PARAM: str = "q"
    _STRUCTURED_QUERY_PARAM: str = "structuredQuery"
    _OPTIONS_PARAM: str = "options"
    _DATABASE_PARAM: str = "database"
    _VIEW_PARAM: str = "view"
    _FORMAT_PARAM: str = "format"
    _COLLECTION_PARAM: str = "collection"
    _DIRECTORY_PARAM: str = "directory"
    _DIRECTION_PARAM: str = "direction"
    _FREQUENCY_PARAM: str = "frequency"
    _LIMIT_PARAM: str = "limit"
    _START_PARAM: str = "start"
    _PAGE_LENGTH_PARAM: str = "pageLength"
    _AGGREGATE_PARAM: str = "aggregate"
    _AGGREGATE_PATH_PARAM: str = "aggregatePath"
    _TRANSFORM_PARAM: str = "transform"
    _TIMESTAMP_PARAM: str = "timestamp"
    _TXID_PARAM: str = "txid"
    _FOREST_NAME_PARAM: str = "forest-name"

    _SUPPORTED_FORMATS: ClassVar[list] = ["json", "xml"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["values", "aggregate", "all"]
    _SUPPORTED_DIRECTIONS: ClassVar[list] = ["ascending", "descending"]
    _SUPPORTED_FREQUENCIES: ClassVar[list] = ["item", "fragment"]

    def __init__(self, name: str, **kwargs):
        """Initialize the shared part of a /v1/values/{name} call.

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        **kwargs
            ApiCall arguments: method, body, accept and content_type.
        """
        super().__init__(**kwargs)
        self._name = name

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Value call.

        Returns
        -------
        str
            A Value call endpoint with the definition name percent-encoded
        """
        return self._ENDPOINT_TEMPLATE.format(
            self._API_VERSION,
            quote(self._name, safe=""),
        )

    @classmethod
    def _validate_params(
        cls,
        name: str,
        view: str | None,
        data_format: str,
        direction: str | None,
        frequency: str | None,
    ):
        """Reject a missing name and enumerated values MarkLogic does not accept.

        Parameters
        ----------
        name : str
            A values or tuples definition name.
        view : str | None
            A values response view.
        data_format : str
            A response format.
        direction : str | None
            A sort direction.
        frequency : str | None
            A frequency calculation method.

        Raises
        ------
        WrongParametersError
            If the name is blank, the format is omitted, or a value, including
            an empty string, is outside its case-sensitive set.
        """
        if not name or not name.strip():
            msg = "No values name provided for /v1/values/{name}!"
            raise exceptions.WrongParametersError(msg)
        utils.validate_supported(view, cls._SUPPORTED_VIEWS, "views")
        utils.validate_supported(
            data_format,
            cls._SUPPORTED_FORMATS,
            "formats",
            required=True,
        )
        utils.validate_supported(direction, cls._SUPPORTED_DIRECTIONS, "directions")
        utils.validate_supported(frequency, cls._SUPPORTED_FREQUENCIES, "frequencies")


class ValueGetCall(_ValueCall):
    """A GET request to query the values in a lexicon or range index.

    An ApiCall implementation representing a single GET request
    to the /v1/values/{name} endpoint.

    Query the values in a lexicon or range index, or find co-occurrences
    of values in multiple range indexes. Optionally apply an aggregate function
    to the values or co-occurrences.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/values/[name]
    """

    def __init__(
        self,
        name: str,
        q: str | None = None,
        structured_query: str | None = None,
        options: str | None = None,
        database: str | None = None,
        view: str | None = None,
        data_format: str = "xml",
        collection: str | list | None = None,
        directory: str | None = None,
        direction: str | None = None,
        frequency: str | None = None,
        limit: int | None = None,
        start: int | None = None,
        page_length: int | None = None,
        aggregate: str | None = None,
        aggregate_path: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        txid: str | None = None,
        forest_name: str | list | None = None,
    ):
        """Initialize ValueGetCall instance.

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        q : str
            A string query.
        structured_query : str
            A serialized structured query or cts:query. This query constrains
            the returned values to those occurring in documents that match the query.
        options : str
            The name of query options previously created via a PUT or POST
            request to the /v1/config/query service.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        view : str
            The view of the query results to return in the response.
            Accepted values: values, aggregate, all. Default: all.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        collection : str | list
            Filter results to include only matches in the named collection.
            Multiple collections are OR related.
        directory : str
            Filter results to include only matches from documents in the
            specified database directory.
        direction : str
            The sort order of returned results. Accepted values: ascending or
            descending. The default direction depends on the sort order defined
            in the options.
        frequency : str
            The method of calculating frequency. Accepted values: item (default)
            or fragment.
        limit : int
            The maximum number of values or tuples to retrieve from the lexicon.
            Default: No limit.
        start : int
            The index of the first result to return from the subset defined
            by limit. Results are numbered beginning with 1. Default: 1.
        page_length : int
            The number of values to return within the subset of values defined
            by limit, beginning with the value selected by start.
            Default: Return all selected values.
        aggregate : str
            The name of a built-in or user-defined aggregate function to run
            against the lexicon. A user-defined function requires aggregate_path.
        aggregate_path : str
            The path to the native plugin library containing the implementation
            of the function named by the aggregate function.
        transform : str
            Names a search result transformation previously installed via
            the /transforms service.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to fetch results at a fixed point-in-time.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        forest_name : str | list
            The name of forest(s) to which results should be limited.
        """
        self._validate_params(name, view, data_format, direction, frequency)
        super().__init__(
            name,
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._params.update(
            utils.query_params(
                {
                    self._Q_PARAM: q,
                    self._STRUCTURED_QUERY_PARAM: structured_query,
                    self._OPTIONS_PARAM: options,
                    self._DATABASE_PARAM: database,
                    self._VIEW_PARAM: view,
                    self._FORMAT_PARAM: data_format,
                    self._COLLECTION_PARAM: collection,
                    self._DIRECTORY_PARAM: directory,
                    self._DIRECTION_PARAM: direction,
                    self._FREQUENCY_PARAM: frequency,
                    self._LIMIT_PARAM: limit,
                    self._START_PARAM: start,
                    self._PAGE_LENGTH_PARAM: page_length,
                    self._AGGREGATE_PARAM: aggregate,
                    self._AGGREGATE_PATH_PARAM: aggregate_path,
                    self._TRANSFORM_PARAM: transform,
                    self._TIMESTAMP_PARAM: timestamp,
                    self._TXID_PARAM: txid,
                    self._FOREST_NAME_PARAM: forest_name,
                },
                transform_params,
            ),
        )


class ValuePostCall(_ValueCall):
    """A POST request to query lexicon values with a query in the request body.

    An ApiCall implementation representing a single POST request
    to the /v1/values/{name} endpoint.

    Query the values in a lexicon or range index, or find co-occurrences
    of values in multiple range indexes. Optionally apply an aggregate function
    to the values or co-occurrences. Query and query options are passed in
    the POST body.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/values/[name]
    """

    def __init__(
        self,
        name: str,
        body: str | dict,
        q: str | None = None,
        options: str | None = None,
        database: str | None = None,
        view: str | None = None,
        data_format: str = "xml",
        txid: str | None = None,
        collection: str | list | None = None,
        direction: str | None = None,
        directory: str | None = None,
        frequency: str | None = None,
        limit: int | None = None,
        start: int | None = None,
        page_length: int | None = None,
        aggregate: str | None = None,
        aggregate_path: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        forest_name: str | list | None = None,
    ):
        """Initialize ValuePostCall instance.

        Parameters
        ----------
        name : str
            The name of a values or tuples definition, in the query options
            from the request body or from the named options.
        body : str | dict
            A query and/or query options, usually a combined query, in XML or JSON.
        q : str
            A string query. This query is AND'd with the query(s) in the request
            body.
        options : str
            The name of query options previously created via a PUT or POST
            request to the /v1/config/query service.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        view : str
            The view of the query results to return in the response.
            Accepted values: values, aggregate, all. Default: all.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list
            Filter results to include only matches in the named collection.
            Multiple collections are OR related.
        direction : str
            The sort order of returned results. Accepted values: ascending or
            descending.
        directory : str
            Filter results to include only matches from documents in the
            specified database directory.
        frequency : str
            The method of calculating frequency. Accepted values: item (default)
            or fragment.
        limit : int
            The maximum number of values or tuples to retrieve from the lexicon.
            Default: No limit.
        start : int
            The index of the first result to return from the subset defined
            by limit. Results are numbered beginning with 1. Default: 1.
        page_length : int
            The number of values to return within the subset of values defined
            by limit, beginning with the value selected by start.
            Default: Return all selected values.
        aggregate : str
            The name of a built-in or user-defined aggregate function to run
            against the lexicon. A user-defined function requires aggregate_path.
        aggregate_path : str
            The path to the native plugin library containing the implementation
            of the function named by the aggregate function.
        transform : str
            Names a search result transformation previously installed via
            the /transforms service.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to fetch results at a fixed point-in-time.
        forest_name : str | list
            The name of forest(s) to which results should be limited.
        """
        self._validate_params(name, view, data_format, direction, frequency)
        body, content_type = utils.request_body_with_content_type(
            body,
            "POST /v1/values/{name}",
        )
        super().__init__(
            name,
            method=constants.METHOD_POST,
            body=body,
            accept=utils.get_accept_header_for_format(data_format),
            content_type=content_type,
        )
        self._params.update(
            utils.query_params(
                {
                    self._Q_PARAM: q,
                    self._OPTIONS_PARAM: options,
                    self._DATABASE_PARAM: database,
                    self._VIEW_PARAM: view,
                    self._FORMAT_PARAM: data_format,
                    self._TXID_PARAM: txid,
                    self._COLLECTION_PARAM: collection,
                    self._DIRECTION_PARAM: direction,
                    self._DIRECTORY_PARAM: directory,
                    self._FREQUENCY_PARAM: frequency,
                    self._LIMIT_PARAM: limit,
                    self._START_PARAM: start,
                    self._PAGE_LENGTH_PARAM: page_length,
                    self._AGGREGATE_PARAM: aggregate,
                    self._AGGREGATE_PATH_PARAM: aggregate_path,
                    self._TRANSFORM_PARAM: transform,
                    self._TIMESTAMP_PARAM: timestamp,
                    self._FOREST_NAME_PARAM: forest_name,
                },
                transform_params,
            ),
        )
