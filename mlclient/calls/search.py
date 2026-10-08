"""The ML Search Api Calls module.

It exports 3 classes:
    * SearchGetCall
        A GET request to search the database or read matching documents.
    * SearchPostCall
        A POST request to search the database using a query in the request body.
    * SearchDeleteCall
        A DELETE request to remove documents in a collection or directory.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import _constants as constants, _utils as utils, exceptions
from mlclient.calls.base import ApiCall
from mlclient.models.document_parts import Category


class _SearchCall(ApiCall):
    """Query parameters, validation and endpoint shared by /v1/search reads."""

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/search"

    _Q_PARAM: str = "q"
    _STRUCTURED_QUERY_PARAM: str = "structuredQuery"
    _START_PARAM: str = "start"
    _PAGE_LENGTH_PARAM: str = "pageLength"
    _OPTIONS_PARAM: str = "options"
    _VIEW_PARAM: str = "view"
    _CATEGORY_PARAM: str = "category"
    _DATABASE_PARAM: str = "database"
    _FORMAT_PARAM: str = "format"
    _TXID_PARAM: str = "txid"
    _COLLECTION_PARAM: str = "collection"
    _DIRECTORY_PARAM: str = "directory"
    _TRANSFORM_PARAM: str = "transform"
    _TIMESTAMP_PARAM: str = "timestamp"
    _FOREST_NAME_PARAM: str = "forest-name"

    _SUPPORTED_FORMATS: ClassVar[list] = ["json", "xml"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["facets", "results", "metadata", "all", "none"]
    _SUPPORTED_CATEGORIES: ClassVar[list] = [category.value for category in Category]

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Search call.

        Returns
        -------
        str
            A Search call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        view: str | None,
        category: str | list | tuple | None,
        data_format: str | None,
        *,
        multipart: bool,
    ):
        """Reject enumerated values and combinations MarkLogic does not accept.

        Parameters
        ----------
        view : str | None
            A search response view.
        category : str | list | tuple | None
            One or more document data categories.
        data_format : str | None
            A response format.
        multipart : bool
            Whether the request is a multi-document read.

        Raises
        ------
        WrongParametersError
            If any value, including an empty string, is outside its supported,
            case-sensitive set, or a category is given outside a multi-document
            read, which MarkLogic rejects with REST-UNSUPPORTEDPARAM.
        """
        utils.validate_supported(view, cls._SUPPORTED_VIEWS, "views")
        utils.validate_supported(category, cls._SUPPORTED_CATEGORIES, "categories")
        utils.validate_supported(data_format, cls._SUPPORTED_FORMATS, "formats")
        if category is not None and not multipart:
            msg = "category is supported only in a multi-document read (multipart=True)"
            raise exceptions.WrongParametersError(msg)

    @staticmethod
    def _accept_header(data_format: str | None, multipart: bool) -> str | None:
        """Return the Accept header selecting a search or a multi-document read.

        Parameters
        ----------
        data_format : str | None
            A response format, used when the request is not a multi-document read.
        multipart : bool
            Whether matching documents are requested.

        Returns
        -------
        str | None
            multipart/mixed, the format's MIME type, or None for the server default.
        """
        if multipart:
            return constants.HEADER_MULTIPART_MIXED
        if data_format:
            return utils.get_accept_header_for_format(data_format)
        return None


class SearchGetCall(_SearchCall):
    """A GET request to search the database or read matching documents.

    An ApiCall implementation representing a single GET request
    to the /v1/search endpoint.

    Search the database using a string query, structured query, or cts:query.
    You can request search results and/or matching documents in the response.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/search
    """

    def __init__(
        self,
        q: str | None = None,
        structured_query: str | None = None,
        start: int | None = None,
        page_length: int | None = None,
        options: str | None = None,
        view: str | None = None,
        category: str | list | None = None,
        database: str | None = None,
        data_format: str | None = None,
        txid: str | None = None,
        collection: str | list | None = None,
        directory: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        forest_name: str | list | None = None,
        multipart: bool = False,
    ):
        """Initialize SearchGetCall instance.

        Parameters
        ----------
        q : str
            A string query expressed in the Search API grammar.
        structured_query : str
            A structured query or cts:query as a string. That is, a serialized
            representation of a search:query element or a cts:query.
        start : int
            The index of the first result to return. Results are numbered
            beginning with 1. Default: 1.
        page_length : int
            The maximum number of results to return in this request.
            Default: 10, or the length configured by the query options.
        options : str
            The name of query options previously created via a PUT or POST
            request to the /v1/config/query service.
        view : str
            The view of the search results to return in the response.
            Accepted values: facets, results, metadata, all, none.
            Default: all for a normal search, none for a multi-document read.
        category : str | list
            The category of data to fetch about the matching documents. Category
            can be specified multiple times to retrieve any combination of content
            and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content. You can only
            use this parameter when making a multi-document read request.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        data_format : str
            For a normal search operation, an Accept header override; it affects
            the content type of the response search results. For a multi-document
            read, it specifies the content type of returned metadata and the search
            results (if requested); it has no effect on returned document content.
            Accepted values: json or xml. Default: xml.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list
            Filter search results to include only matches in the named collection.
            If you specify this parameter multiple times, the collections are
            OR related.
        directory : str
            Filter search results to include only matches from documents in
            the specified database directory.
        transform : str
            Names a search result transformation previously installed via
            the /transforms service.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request. Use this parameter to iteratively fetch search results based
            on the contents of the database at a fixed point-in-time.
        forest_name : str | list
            The name of forest(s) to which results should be limited.
        multipart : bool, default False
            Request a multi-document read (Accept: multipart/mixed) returning
            matching content and/or metadata instead of only search results.
        """
        self._validate_params(view, category, data_format, multipart=multipart)
        super().__init__(
            method=constants.METHOD_GET,
            accept=self._accept_header(data_format, multipart),
        )
        self._params.update(
            utils.query_params(
                {
                    self._Q_PARAM: q,
                    self._STRUCTURED_QUERY_PARAM: structured_query,
                    self._START_PARAM: start,
                    self._PAGE_LENGTH_PARAM: page_length,
                    self._OPTIONS_PARAM: options,
                    self._VIEW_PARAM: view,
                    self._CATEGORY_PARAM: category,
                    self._DATABASE_PARAM: database,
                    self._FORMAT_PARAM: data_format,
                    self._TXID_PARAM: txid,
                    self._COLLECTION_PARAM: collection,
                    self._DIRECTORY_PARAM: directory,
                    self._TRANSFORM_PARAM: transform,
                    self._TIMESTAMP_PARAM: timestamp,
                    self._FOREST_NAME_PARAM: forest_name,
                },
                transform_params,
            ),
        )


class SearchPostCall(_SearchCall):
    """A POST request to search the database using a query in the request body.

    An ApiCall implementation representing a single POST request
    to the /v1/search endpoint.

    Search the database using a string query, structured query, a cts:query,
    or a combined query in the POST body. Returns search results, matching
    content and/or metadata, or both.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/search
    """

    def __init__(
        self,
        body: str | dict,
        q: str | None = None,
        start: int | None = None,
        page_length: int | None = None,
        options: str | None = None,
        view: str | None = None,
        category: str | list | None = None,
        database: str | None = None,
        data_format: str | None = None,
        txid: str | None = None,
        collection: str | list | None = None,
        directory: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        timestamp: str | None = None,
        forest_name: str | list | None = None,
        multipart: bool = False,
    ):
        """Initialize SearchPostCall instance.

        Parameters
        ----------
        body : str | dict
            A string, structured, cts or combined query in XML or JSON format.
        q : str
            A string query conforming to the Search API grammar.
            This query is AND'd with the query(s) in the request body.
        start : int
            The index of the first result to return. The first result is index 1.
            Default: 1.
        page_length : int
            The maximum number of results to return in this request.
            Default: 10, or the length configured by the query options.
        options : str
            The name of query options previously created via a PUT or POST
            request to the /v1/config/query service.
        view : str
            The view of the search results to return in the response.
            Accepted values: facets, results, metadata, all, none.
            Default: all for a normal search, none for a multi-document read.
        category : str | list
            The category of data to fetch about the matching documents. Valid
            categories: content (default), metadata, metadata-values, collections,
            permissions, properties, and quality. You can only use this parameter
            when making a multi-document read request.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        data_format : str
            Indicates the input and/or output content type, in conjunction with
            or instead of the Content-type and Accept headers. The format
            parameter always takes precedence over the Accept header.
            Accepted values: json or xml.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list
            Filter search results so they include only matches in the named
            collection. Multiple collections are OR related.
        directory : str
            Filter search results so they only include matches from documents in
            the specified database directory.
        transform : str
            Names a search result transformation previously installed via
            the /transforms service. On a multi-document read request, the
            transform is applied to each returned document as well as the search
            response (if a search response is requested).
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to fetch search results at a fixed point-in-time.
        forest_name : str | list
            The name of forest(s) to which results should be limited.
        multipart : bool, default False
            Request a multi-document read (Accept: multipart/mixed) returning
            matching content and/or metadata instead of only search results.
        """
        self._validate_params(view, category, data_format, multipart=multipart)
        body, content_type = utils.request_body_with_content_type(
            body,
            "POST /v1/search",
        )
        super().__init__(
            method=constants.METHOD_POST,
            body=body,
            accept=self._accept_header(data_format, multipart),
            content_type=content_type,
        )
        self._params.update(
            utils.query_params(
                {
                    self._Q_PARAM: q,
                    self._START_PARAM: start,
                    self._PAGE_LENGTH_PARAM: page_length,
                    self._OPTIONS_PARAM: options,
                    self._VIEW_PARAM: view,
                    self._CATEGORY_PARAM: category,
                    self._DATABASE_PARAM: database,
                    self._FORMAT_PARAM: data_format,
                    self._TXID_PARAM: txid,
                    self._COLLECTION_PARAM: collection,
                    self._DIRECTORY_PARAM: directory,
                    self._TRANSFORM_PARAM: transform,
                    self._TIMESTAMP_PARAM: timestamp,
                    self._FOREST_NAME_PARAM: forest_name,
                },
                transform_params,
            ),
        )


class SearchDeleteCall(ApiCall):
    """A DELETE request to remove documents in a collection or directory.

    An ApiCall implementation representing a single DELETE request
    to the /v1/search endpoint.

    Remove documents in a collection or directory, or clear the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/v1/search
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/search"

    _DATABASE_PARAM: str = "database"
    _TXID_PARAM: str = "txid"
    _COLLECTION_PARAM: str = "collection"
    _DIRECTORY_PARAM: str = "directory"

    def __init__(
        self,
        database: str | None = None,
        txid: str | None = None,
        collection: str | None = None,
        directory: str | None = None,
        *,
        clear_database: bool = False,
    ):
        """Initialize SearchDeleteCall instance.

        Without a collection or directory the request clears the whole content
        database, which requires the rest-admin role. That request is built only
        when clear_database confirms it.

        Parameters
        ----------
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str
            Remove documents in the named collection.
        directory : str
            Remove documents in the named directory.
        clear_database : bool, default False
            Confirm removing every document in the database. Required when
            neither a collection nor a directory is given; rejected with one.

        Raises
        ------
        WrongParametersError
            If a supplied filter is not a string, if an explicitly supplied
            parameter is blank, if neither filter is given without
            clear_database, or if clear_database is combined with a filter.
        """
        params = {
            self._DATABASE_PARAM: database,
            self._TXID_PARAM: txid,
            self._COLLECTION_PARAM: collection,
            self._DIRECTORY_PARAM: directory,
        }
        for name, value in params.items():
            if (
                name in {self._COLLECTION_PARAM, self._DIRECTORY_PARAM}
                and value is not None
                and not isinstance(value, str)
            ):
                message = f"{name} must be a string in DELETE /v1/search"
                raise exceptions.WrongParametersError(message)
            if isinstance(value, str) and not value.strip():
                message = f"{name} must not be blank in DELETE /v1/search"
                raise exceptions.WrongParametersError(message)
        _validate_delete_scope(collection, directory, clear_database=clear_database)
        super().__init__(method=constants.METHOD_DELETE)
        self._params = {
            name: value for name, value in params.items() if value is not None
        }

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Search call.

        Returns
        -------
        str
            A Search call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)


def _validate_delete_scope(
    collection: str | None,
    directory: str | None,
    *,
    clear_database: bool,
):
    """Require explicit confirmation before a DELETE clears the whole database.

    Parameters
    ----------
    collection : str | None
        The collection whose documents are removed.
    directory : str | None
        The directory whose documents are removed.
    clear_database : bool
        Whether the caller confirmed removing every document in the database.

    Raises
    ------
    WrongParametersError
        If no filter is given without confirmation, or a filter is combined
        with the confirmation.
    """
    has_filter = collection is not None or directory is not None
    if not has_filter and not clear_database:
        message = (
            "DELETE /v1/search without a collection or directory removes every "
            "document in the database; pass clear_database=True to confirm"
        )
        raise exceptions.WrongParametersError(message)
    if has_filter and clear_database:
        message = (
            "clear_database=True removes every document in the database "
            "and cannot be combined with a collection or directory"
        )
        raise exceptions.WrongParametersError(message)
