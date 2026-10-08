"""SearchApi / AsyncSearchApi - MarkLogic search endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.search import SearchDeleteCall, SearchGetCall, SearchPostCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class SearchApi:
    """Mid-level API for ``/v1/search`` endpoints.

    Search documents, read documents matching a query, or remove documents.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def get(
        self,
        *,
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
        timeout=UNSET,
    ) -> Response:
        """Search the database using a string query, structured query, or cts:query.

        Documentation: https://docs.marklogic.com/REST/GET/v1/search

        Parameters
        ----------
        q : str | None
            A string query expressed in the Search API grammar.
        structured_query : str | None
            A serialized structured query or cts:query.
        start : int | None
            The index of the first result to return. Results are numbered beginning
            with 1.
        page_length : int | None
            The maximum number of results to return in this request.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        view : str | None
            The view of the search results: facets, results, metadata, all or none.
        category : str | list | None
            The category of data to fetch about matching documents in a multi-
            document read: content (default), metadata, metadata-values,
            collections, permissions, properties or quality.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        data_format : str | None
            The format of the returned search results or metadata: json or xml.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        multipart : bool
            Request a multi-document read (Accept: multipart/mixed) returning
            matching content and/or metadata instead of search results.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with search results or matching documents

        Raises
        ------
        WrongParametersError
            If an enumerated value is unsupported, or a category is given without
            multipart.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = SearchGetCall(
            q=q,
            structured_query=structured_query,
            start=start,
            page_length=page_length,
            options=options,
            view=view,
            category=category,
            database=database,
            data_format=data_format,
            txid=txid,
            collection=collection,
            directory=directory,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            forest_name=forest_name,
            multipart=multipart,
        )
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        body: str | dict,
        *,
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
        timeout=UNSET,
    ) -> Response:
        """Search the database using a query or combined query in the POST body.

        Documentation: https://docs.marklogic.com/REST/POST/v1/search

        Parameters
        ----------
        body : str | dict
            A string, structured, cts or combined query in XML or JSON format.
        q : str | None
            A string query, AND'd with the query(s) in the request body.
        start : int | None
            The index of the first result to return. Results are numbered beginning
            with 1.
        page_length : int | None
            The maximum number of results to return in this request.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        view : str | None
            The view of the search results: facets, results, metadata, all or none.
        category : str | list | None
            The category of data to fetch about matching documents in a multi-
            document read: content (default), metadata, metadata-values,
            collections, permissions, properties or quality.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        data_format : str | None
            The format of the returned search results or metadata: json or xml.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        multipart : bool
            Request a multi-document read (Accept: multipart/mixed) returning
            matching content and/or metadata instead of search results.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with search results or matching documents

        Raises
        ------
        WrongParametersError
            If the body is missing, blank or JSON other than an object, an enumerated
            value is unsupported, or a category is given without multipart.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = SearchPostCall(
            body=body,
            q=q,
            start=start,
            page_length=page_length,
            options=options,
            view=view,
            category=category,
            database=database,
            data_format=data_format,
            txid=txid,
            collection=collection,
            directory=directory,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            forest_name=forest_name,
            multipart=multipart,
        )
        return self._api.call(call, timeout=timeout)

    def delete(
        self,
        *,
        database: str | None = None,
        txid: str | None = None,
        collection: str | None = None,
        directory: str | None = None,
        clear_database: bool = False,
        timeout=UNSET,
    ) -> Response:
        """Remove documents in a collection or directory, or clear the database.

        Documentation: https://docs.marklogic.com/REST/DELETE/v1/search

        Parameters
        ----------
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | None
            Remove documents in the named collection.
        directory : str | None
            Remove documents in the named directory.
        clear_database : bool, default False
            Confirm removing every document in the database. Required when
            neither a collection nor a directory is given; rejected with one.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response; 204 on success.

        Raises
        ------
        WrongParametersError
            If an explicitly supplied parameter is blank, if neither filter is
            given without clear_database, or if clear_database is combined with
            a filter. Raised before any request is sent.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = SearchDeleteCall(
            database=database,
            txid=txid,
            collection=collection,
            directory=directory,
            clear_database=clear_database,
        )
        return self._api.call(call, timeout=timeout)


class AsyncSearchApi:
    """Async mid-level API for ``/v1/search`` endpoints.

    Search documents, read documents matching a query, or remove documents.
    """

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get(
        self,
        *,
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
        timeout=UNSET,
    ) -> Response:
        """Search the database using a string query, structured query, or cts:query.

        Documentation: https://docs.marklogic.com/REST/GET/v1/search

        Parameters
        ----------
        q : str | None
            A string query expressed in the Search API grammar.
        structured_query : str | None
            A serialized structured query or cts:query.
        start : int | None
            The index of the first result to return. Results are numbered beginning
            with 1.
        page_length : int | None
            The maximum number of results to return in this request.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        view : str | None
            The view of the search results: facets, results, metadata, all or none.
        category : str | list | None
            The category of data to fetch about matching documents in a multi-
            document read: content (default), metadata, metadata-values,
            collections, permissions, properties or quality.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        data_format : str | None
            The format of the returned search results or metadata: json or xml.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        multipart : bool
            Request a multi-document read (Accept: multipart/mixed) returning
            matching content and/or metadata instead of search results.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with search results or matching documents

        Raises
        ------
        WrongParametersError
            If an enumerated value is unsupported, or a category is given without
            multipart.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = SearchGetCall(
            q=q,
            structured_query=structured_query,
            start=start,
            page_length=page_length,
            options=options,
            view=view,
            category=category,
            database=database,
            data_format=data_format,
            txid=txid,
            collection=collection,
            directory=directory,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            forest_name=forest_name,
            multipart=multipart,
        )
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        body: str | dict,
        *,
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
        timeout=UNSET,
    ) -> Response:
        """Search the database using a query or combined query in the POST body.

        Documentation: https://docs.marklogic.com/REST/POST/v1/search

        Parameters
        ----------
        body : str | dict
            A string, structured, cts or combined query in XML or JSON format.
        q : str | None
            A string query, AND'd with the query(s) in the request body.
        start : int | None
            The index of the first result to return. Results are numbered beginning
            with 1.
        page_length : int | None
            The maximum number of results to return in this request.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        view : str | None
            The view of the search results: facets, results, metadata, all or none.
        category : str | list | None
            The category of data to fetch about matching documents in a multi-
            document read: content (default), metadata, metadata-values,
            collections, permissions, properties or quality.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        data_format : str | None
            The format of the returned search results or metadata: json or xml.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        multipart : bool
            Request a multi-document read (Accept: multipart/mixed) returning
            matching content and/or metadata instead of search results.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with search results or matching documents

        Raises
        ------
        WrongParametersError
            If the body is missing, blank or JSON other than an object, an enumerated
            value is unsupported, or a category is given without multipart.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = SearchPostCall(
            body=body,
            q=q,
            start=start,
            page_length=page_length,
            options=options,
            view=view,
            category=category,
            database=database,
            data_format=data_format,
            txid=txid,
            collection=collection,
            directory=directory,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            forest_name=forest_name,
            multipart=multipart,
        )
        return await self._api.call(call, timeout=timeout)

    async def delete(
        self,
        *,
        database: str | None = None,
        txid: str | None = None,
        collection: str | None = None,
        directory: str | None = None,
        clear_database: bool = False,
        timeout=UNSET,
    ) -> Response:
        """Remove documents in a collection or directory, or clear the database.

        Documentation: https://docs.marklogic.com/REST/DELETE/v1/search

        Parameters
        ----------
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        collection : str | None
            Remove documents in the named collection.
        directory : str | None
            Remove documents in the named directory.
        clear_database : bool, default False
            Confirm removing every document in the database. Required when
            neither a collection nor a directory is given; rejected with one.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response; 204 on success.

        Raises
        ------
        WrongParametersError
            If an explicitly supplied parameter is blank, if neither filter is
            given without clear_database, or if clear_database is combined with
            a filter. Raised before any request is sent.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = SearchDeleteCall(
            database=database,
            txid=txid,
            collection=collection,
            directory=directory,
            clear_database=clear_database,
        )
        return await self._api.call(call, timeout=timeout)
