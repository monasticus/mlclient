"""ValuesApi / AsyncValuesApi - MarkLogic values endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient._options import UNSET
from mlclient.calls.values import ValueGetCall, ValuePostCall, ValuesGetCall

if TYPE_CHECKING:
    from mlclient.clients.api import ApiClient, AsyncApiClient


class ValuesApi:
    """Mid-level API for ``/v1/values`` endpoints.

    Query lexicon and range index values, co-occurrences and aggregates.
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def get_list(
        self,
        *,
        database: str | None = None,
        data_format: str = "xml",
        options: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """List lexicon configurations available for use with GET /v1/values/{name}.

        Documentation: https://docs.marklogic.com/REST/GET/v1/values

        Parameters
        ----------
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        options : str | None
            The query options for which to list available lexicon configurations.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with named lexicon configurations

        Raises
        ------
        WrongParametersError
            If the format is omitted or unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ValuesGetCall(
            database=database,
            data_format=data_format,
            options=options,
        )
        return self._api.call(call, timeout=timeout)

    def get(
        self,
        name: str,
        *,
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
        timeout=UNSET,
    ) -> Response:
        """Query the values in a lexicon or range index, optionally aggregating them.

        Documentation: https://docs.marklogic.com/REST/GET/v1/values/[name]

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        q : str | None
            A string query constraining the returned values.
        structured_query : str | None
            A serialized structured query or cts:query constraining the returned
            values.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        view : str | None
            The view of the results: values, aggregate or all.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        direction : str | None
            The sort order of returned results: ascending or descending.
        frequency : str | None
            The method of calculating frequency: item (default) or fragment.
        limit : int | None
            The maximum number of values or tuples to retrieve from the lexicon.
        start : int | None
            The index of the first result to return from the subset defined by
            limit.
        page_length : int | None
            The number of values to return within the subset defined by limit.
        aggregate : str | None
            The name of a built-in or user-defined aggregate function to run against
            the lexicon.
        aggregate_path : str | None
            The path to the native plugin library implementing a user-defined
            aggregate.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with values, tuples or aggregates

        Raises
        ------
        WrongParametersError
            If the name is blank or an enumerated value is omitted or unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ValueGetCall(
            name=name,
            q=q,
            structured_query=structured_query,
            options=options,
            database=database,
            view=view,
            data_format=data_format,
            collection=collection,
            directory=directory,
            direction=direction,
            frequency=frequency,
            limit=limit,
            start=start,
            page_length=page_length,
            aggregate=aggregate,
            aggregate_path=aggregate_path,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            txid=txid,
            forest_name=forest_name,
        )
        return self._api.call(call, timeout=timeout)

    def post(
        self,
        name: str,
        body: str | dict,
        *,
        q: str | None = None,
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
        timeout=UNSET,
    ) -> Response:
        """Query lexicon values with a query and/or query options in the POST body.

        Documentation: https://docs.marklogic.com/REST/POST/v1/values/[name]

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        body : str | dict
            A query and/or query options, usually a combined query, in XML or JSON.
        q : str | None
            A string query, AND'd with the query(s) in the request body.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        view : str | None
            The view of the results: values, aggregate or all.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        direction : str | None
            The sort order of returned results: ascending or descending.
        frequency : str | None
            The method of calculating frequency: item (default) or fragment.
        limit : int | None
            The maximum number of values or tuples to retrieve from the lexicon.
        start : int | None
            The index of the first result to return from the subset defined by
            limit.
        page_length : int | None
            The number of values to return within the subset defined by limit.
        aggregate : str | None
            The name of a built-in or user-defined aggregate function to run against
            the lexicon.
        aggregate_path : str | None
            The path to the native plugin library implementing a user-defined
            aggregate.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with values, tuples or aggregates

        Raises
        ------
        WrongParametersError
            If the name is blank, the body is missing, blank or JSON other than an
            object, or an enumerated value is omitted or unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ValuePostCall(
            name=name,
            body=body,
            q=q,
            options=options,
            database=database,
            view=view,
            data_format=data_format,
            collection=collection,
            directory=directory,
            direction=direction,
            frequency=frequency,
            limit=limit,
            start=start,
            page_length=page_length,
            aggregate=aggregate,
            aggregate_path=aggregate_path,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            txid=txid,
            forest_name=forest_name,
        )
        return self._api.call(call, timeout=timeout)


class AsyncValuesApi:
    """Async mid-level API for ``/v1/values`` endpoints.

    Query lexicon and range index values, co-occurrences and aggregates.
    """

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def get_list(
        self,
        *,
        database: str | None = None,
        data_format: str = "xml",
        options: str | None = None,
        timeout=UNSET,
    ) -> Response:
        """List lexicon configurations available for use with GET /v1/values/{name}.

        Documentation: https://docs.marklogic.com/REST/GET/v1/values

        Parameters
        ----------
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        options : str | None
            The query options for which to list available lexicon configurations.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with named lexicon configurations

        Raises
        ------
        WrongParametersError
            If the format is omitted or unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ValuesGetCall(
            database=database,
            data_format=data_format,
            options=options,
        )
        return await self._api.call(call, timeout=timeout)

    async def get(
        self,
        name: str,
        *,
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
        timeout=UNSET,
    ) -> Response:
        """Query the values in a lexicon or range index, optionally aggregating them.

        Documentation: https://docs.marklogic.com/REST/GET/v1/values/[name]

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        q : str | None
            A string query constraining the returned values.
        structured_query : str | None
            A serialized structured query or cts:query constraining the returned
            values.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        view : str | None
            The view of the results: values, aggregate or all.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        direction : str | None
            The sort order of returned results: ascending or descending.
        frequency : str | None
            The method of calculating frequency: item (default) or fragment.
        limit : int | None
            The maximum number of values or tuples to retrieve from the lexicon.
        start : int | None
            The index of the first result to return from the subset defined by
            limit.
        page_length : int | None
            The number of values to return within the subset defined by limit.
        aggregate : str | None
            The name of a built-in or user-defined aggregate function to run against
            the lexicon.
        aggregate_path : str | None
            The path to the native plugin library implementing a user-defined
            aggregate.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with values, tuples or aggregates

        Raises
        ------
        WrongParametersError
            If the name is blank or an enumerated value is omitted or unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ValueGetCall(
            name=name,
            q=q,
            structured_query=structured_query,
            options=options,
            database=database,
            view=view,
            data_format=data_format,
            collection=collection,
            directory=directory,
            direction=direction,
            frequency=frequency,
            limit=limit,
            start=start,
            page_length=page_length,
            aggregate=aggregate,
            aggregate_path=aggregate_path,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            txid=txid,
            forest_name=forest_name,
        )
        return await self._api.call(call, timeout=timeout)

    async def post(
        self,
        name: str,
        body: str | dict,
        *,
        q: str | None = None,
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
        timeout=UNSET,
    ) -> Response:
        """Query lexicon values with a query and/or query options in the POST body.

        Documentation: https://docs.marklogic.com/REST/POST/v1/values/[name]

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        body : str | dict
            A query and/or query options, usually a combined query, in XML or JSON.
        q : str | None
            A string query, AND'd with the query(s) in the request body.
        options : str | None
            The name of query options previously installed via /v1/config/query.
        database : str | None
            Perform this operation on the named content database instead of the
            default content database associated with the REST API instance. The
            database can be identified by name or by database id.
        view : str | None
            The view of the results: values, aggregate or all.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        collection : str | list | None
            Restrict matches to the named collection(s); multiple collections are OR
            related.
        directory : str | None
            Restrict matches to documents in the specified database directory.
        direction : str | None
            The sort order of returned results: ascending or descending.
        frequency : str | None
            The method of calculating frequency: item (default) or fragment.
        limit : int | None
            The maximum number of values or tuples to retrieve from the lexicon.
        start : int | None
            The index of the first result to return from the subset defined by
            limit.
        page_length : int | None
            The number of values to return within the subset defined by limit.
        aggregate : str | None
            The name of a built-in or user-defined aggregate function to run against
            the lexicon.
        aggregate_path : str | None
            The path to the native plugin library implementing a user-defined
            aggregate.
        transform : str | None
            Names a transformation previously installed via the /transforms service.
        transform_params : dict | None
            Transform parameter names and values, passed to the named transform.
        timestamp : str | None
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request, to read at a fixed point-in-time.
        txid : str | None
            The transaction identifier of the multi-statement transaction in which
            to service this request.
        forest_name : str | list | None
            The name of forest(s) to which results should be limited.
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with values, tuples or aggregates

        Raises
        ------
        WrongParametersError
            If the name is blank, the body is missing, blank or JSON other than an
            object, or an enumerated value is omitted or unsupported.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        """
        call = ValuePostCall(
            name=name,
            body=body,
            q=q,
            options=options,
            database=database,
            view=view,
            data_format=data_format,
            collection=collection,
            directory=directory,
            direction=direction,
            frequency=frequency,
            limit=limit,
            start=start,
            page_length=page_length,
            aggregate=aggregate,
            aggregate_path=aggregate_path,
            transform=transform,
            transform_params=transform_params,
            timestamp=timestamp,
            txid=txid,
            forest_name=forest_name,
        )
        return await self._api.call(call, timeout=timeout)
