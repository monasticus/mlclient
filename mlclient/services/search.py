"""Higher-level REST search service (SearchService / AsyncSearchService).

Runs structured, CTS and string queries through /v1/search and /v1/values
without evaluating XQuery, and parses the responses into mlclient models.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields, replace
from typing import TYPE_CHECKING, Literal
from xml.etree import ElementTree

from mlclient import _constants as constants
from mlclient._options import UNSET
from mlclient.models.document_parts import Category, DocumentsDisposition
from mlclient.models.results import ParsedValue, SearchReport, TupleHit, ValueHit
from mlclient.search.base import SearchQuery
from mlclient.search.options import SearchOptions
from mlclient.search.structured import SEARCH_NS_URI
from mlclient.responses import MLResponseParser
from mlclient.services._documents_parsing import DocumentsReader, normalize_category

if TYPE_CHECKING:
    from httpx import Response

    from mlclient.api.rest import AsyncRestApi, RestApi
    from mlclient.models.documents import Document

SearchInput = SearchQuery | str | None
"""A structured or CTS query, a Search API string query, or None for all."""

PositionInput = int | list[int] | tuple[int, int] | None
"""A one-based position or an inclusive two-position range."""

OptionsInput = str | dict | SearchOptions | None
"""Installed options name, native inline options members, or an options builder."""

Direction = Literal["ascending", "descending"]
"""Lexicon order."""

Frequency = Literal["item", "fragment"]
"""Count occurrences (item) or matching fragments (fragment)."""

ReportView = Literal["all", "results", "facets", "metadata"]
"""Search report sections."""

AggregateFunction = Literal[
    "avg",
    "correlation",
    "count",
    "covariance",
    "covariance-population",
    "max",
    "median",
    "min",
    "stddev",
    "stddev-population",
    "sum",
    "variance",
    "variance-population",
]
"""Built-in lexicon aggregate functions."""

_RANGE_BOUND_COUNT = 2
_DOUBLE_AGGREGATES = frozenset(
    {
        "correlation",
        "covariance",
        "covariance-population",
        "median",
        "stddev",
        "stddev-population",
        "variance",
        "variance-population",
    },
)
_INTEGER_LEXICON_TYPES = frozenset(
    {"xs:int", "xs:long", "xs:unsignedInt", "xs:unsignedLong"},
)


@dataclass(frozen=True)
class SearchScope:
    """Where searches run and which search options apply.

    Every field defaults to unset, meaning inherited: a scope passed to one
    operation overrides only the fields it sets on its service's scope, and
    None explicitly clears an inherited value. A TransactionService unpacks
    into it: ``SearchScope(**txn)``.

    Parameters
    ----------
    database : str | None, default unset
        Content database name or id; None uses the REST server's database.
    txid : str | None, default unset
        Multi-statement transaction to search within.
    collection : str | list[str] | None, default unset
        Restrict matches to one or more OR-related collections.
    directory : str | None, default unset
        Restrict matches to this database directory.
    forest_name : str | list[str] | None, default unset
        Restrict matches to these database forests.
    options : str | dict | SearchOptions | None, default unset
        Installed options name, or inline options members or builder sent in
        the combined query. Inline options do not install configuration; a
        dict is copied, so later changes to it do not affect the scope.
    timestamp : str | None, default unset
        Effective timestamp from an earlier response, for snapshot pagination.

    Raises
    ------
    TypeError
        If options are not a name, dict or SearchOptions, or a dict wraps its
        members in an ``options`` key.
    """

    database: str | None = UNSET
    txid: str | None = UNSET
    collection: str | list[str] | None = UNSET
    directory: str | None = UNSET
    forest_name: str | list[str] | None = UNSET
    options: OptionsInput = UNSET
    timestamp: str | None = UNSET

    def __post_init__(self):
        """Freeze list restrictions to tuples and copy inline options.

        Raises
        ------
        TypeError
            If options are not a name, dict or SearchOptions, or a dict wraps
            its members in an ``options`` key.
        """
        for name in ("collection", "forest_name"):
            if isinstance(getattr(self, name), list):
                object.__setattr__(self, name, tuple(getattr(self, name)))
        if isinstance(self.options, dict):
            _check_inline_options(self.options)
            object.__setattr__(self, "options", copy.deepcopy(self.options))
        elif not isinstance(self.options, (str, SearchOptions)) and (
            self.options is not UNSET and self.options is not None
        ):
            message = (
                "options must be an installed name, inline dictionary or "
                f"SearchOptions, got {type(self.options).__name__}"
            )
            raise TypeError(message)

    def overridden_by(self, other: SearchScope | None) -> SearchScope:
        """Return this scope with every field another scope sets.

        Parameters
        ----------
        other : SearchScope | None
            The overriding scope; None overrides nothing.

        Returns
        -------
        SearchScope
            A new scope; fields unset in other keep this scope's values.

        Raises
        ------
        TypeError
            If other is neither a SearchScope nor None.
        """
        if other is None:
            return self
        if not isinstance(other, SearchScope):
            message = f"scope must be a SearchScope, got {type(other).__name__}"
            raise TypeError(message)
        overrides = {
            field.name: getattr(other, field.name)
            for field in fields(other)
            if getattr(other, field.name) is not UNSET
        }
        return replace(self, **overrides)

    def request_params(self) -> dict:
        """Return the endpoint arguments of every set field except options.

        Options are not a plain argument: installed names are sent as a query
        parameter and inline options in a combined-query body.

        Returns
        -------
        dict
            Endpoint keyword arguments; unset fields are omitted.
        """
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name != "options" and getattr(self, field.name) is not UNSET
        }


def _check_inline_options(options: dict):
    """Reject inline options still wrapped in their ``options`` object.

    Parameters
    ----------
    options : dict
        Inline options members, as the combined query's options member.

    Raises
    ------
    TypeError
        If the only member is ``options``, which is not a search option.
    """
    if options.keys() == {"options"}:
        message = (
            "inline options must be the members of the options object; "
            "pass options['options'] instead of the whole object"
        )
        raise TypeError(message)


class SearchService:
    """Search documents, URIs and lexicon values through the REST Search API.

    Queries are sent as JSON: structured queries as ``{"query": ...}``, CTS
    queries as ``{"ctsquery": ...}``, a string as a Search API string query.
    No XQuery is evaluated, so the REST user needs only the rest-reader role;
    a scope naming another database also needs the xdmp-eval-in privilege.

    The service carries a SearchScope: calling it, as in
    ``ml.search(database="catalog")``, returns a service whose operations all
    use that scope, and an operation's ``scope`` argument overrides it for one
    request.
    """

    def __init__(self, rest: RestApi, scope: SearchScope | None = None):
        """Create the service using the client's REST API.

        Parameters
        ----------
        rest : RestApi
            REST API used to send requests; no request is made here.
        scope : SearchScope | None, default None
            Scope applied to every operation; None searches the REST server's
            database without restrictions or options.
        """
        self._rest = rest
        self._scope = scope if scope is not None else SearchScope()

    def __call__(
        self,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        collection: str | list[str] | None = UNSET,
        directory: str | None = UNSET,
        forest_name: str | list[str] | None = UNSET,
        options: OptionsInput = UNSET,
        timestamp: str | None = UNSET,
    ) -> SearchService:
        """Return a service whose operations use a narrower scope.

        Sends no request. Arguments override this service's scope field by
        field; omitted arguments are inherited and None clears an inherited
        value. A TransactionService unpacks into it: ``ml.search(**txn)``.

        Parameters
        ----------
        database : str | None, default unset
            Content database name or id; None uses the REST server's database.
        txid : str | None, default unset
            Multi-statement transaction to search within.
        collection : str | list[str] | None, default unset
            Restrict matches to one or more OR-related collections.
        directory : str | None, default unset
            Restrict matches to this database directory.
        forest_name : str | list[str] | None, default unset
            Restrict matches to these database forests.
        options : str | dict | SearchOptions | None, default unset
            Installed options name, or inline options members or builder.
        timestamp : str | None, default unset
            Effective timestamp from an earlier response, for snapshot
            pagination.

        Returns
        -------
        SearchService
            A new service bound to the same connection; this one is unchanged.
        """
        narrower = SearchScope(
            database=database,
            txid=txid,
            collection=collection,
            directory=directory,
            forest_name=forest_name,
            options=options,
            timestamp=timestamp,
        )
        return SearchService(self._rest, self._scope.overridden_by(narrower))

    @property
    def scope(self) -> SearchScope:
        """The scope applied to every operation of this service.

        Returns
        -------
        SearchScope
            An immutable scope; fields left unset are not sent.
        """
        return self._scope

    def documents(
        self,
        query: SearchInput = None,
        *,
        pos: PositionInput = None,
        category: Category | str | list[Category | str] | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[Document]:
        """Return documents matching a query, in search result order.

        Sends a multi-document read (GET /v1/search, multipart/mixed, or POST
        with inline options). MarkLogic returns only the documents: no search
        report, snippets or facets.

        Parameters
        ----------
        query : SearchQuery | str | None, default None
            A structured or CTS query, a string query, or None to match all.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range. None returns
            the first page: the page-length of inline options, else 10.
            Installed options' page-length does not apply to this read.
        category : Category | str | list[Category | str] | None, default None
            Document data to return: content (default) and/or metadata categories.
        transform : str | None, default None
            Installed REST response transform applied to the document content.
        transform_params : dict | None, default None
            Named parameters passed to the installed transform.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[Document]
            Matching documents; [] when nothing matches.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        WrongParametersError
            If a category is outside the supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        category = normalize_category(category)
        params = _request_params(self._scope, query, pos, scope)
        resp = self._rest.search.post(
            **params,
            category=category,
            data_format="json",
            transform=transform,
            transform_params=transform_params,
            multipart=True,
            timeout=timeout,
        )
        return _parse_documents(resp, category)

    def uris(
        self,
        query: SearchInput = None,
        *,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[str]:
        """Return URIs of documents matching a query, in search result order.

        Sends a multi-document read of the smallest metadata category (quality)
        and takes each URI from its part's Content-Disposition, so no document
        content or search report is transferred.

        Parameters
        ----------
        query : SearchQuery | str | None, default None
            A structured or CTS query, a string query, or None to match all.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range. None returns
            the first page: the page-length of inline options, else 10.
            Installed options' page-length does not apply to this read.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[str]
            Matching document URIs; [] when nothing matches.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope)
        resp = self._rest.search.post(
            **params,
            category=Category.QUALITY.value,
            data_format="json",
            multipart=True,
            timeout=timeout,
        )
        return _parse_uris(resp)

    def values(
        self,
        name: str,
        query: SearchInput = None,
        *,
        direction: Direction | None = None,
        frequency: Frequency | None = None,
        limit: int | None = None,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[ValueHit]:
        """Return values of a named lexicon definition with their frequencies.

        Sends POST with named or inline options. The values
        definition must exist in the scope's options or the server's default
        options.

        Parameters
        ----------
        name : str
            The name of a values definition in the query options.
        query : SearchQuery | str | None, default None
            Restrict values to documents matching a structured, CTS or string
            query; None reads the whole lexicon.
        direction : {'ascending', 'descending'} | None, default None
            Lexicon order; None uses the options' sort order.
        frequency : {'item', 'fragment'} | None, default None
            Count occurrences (item) or matching fragments (fragment).
        limit : int | None, default None
            Cap the lexicon subset before applying pos; None has no cap.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range of values.
            None returns every value, as the endpoint does.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[ValueHit]
            Values converted from their reported XML Schema type, in lexicon
            order, with their frequencies; [] when there are none.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, a query value has no local
            native form, or the name refers to a tuples definition.
        WrongParametersError
            If the name is blank, or direction or frequency is outside its
            supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope, lexicon=True)
        resp = self._rest.values.post(
            name,
            **params,
            data_format="json",
            view="values",
            direction=direction,
            frequency=frequency,
            limit=limit,
            timeout=timeout,
        )
        return _parse_values(resp)

    def aggregate(
        self,
        name: str,
        function: AggregateFunction,
        query: SearchInput = None,
        *,
        direction: Direction | None = None,
        frequency: Frequency | None = None,
        limit: int | None = None,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> ParsedValue | None:
        """Apply a built-in aggregate to a values or tuples definition.

        Sends POST with named or inline options. The definition
        must exist in the scope's options or the server's default options.

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        function : str
            Built-in aggregate (sum, avg, count, min, max, median, stddev,
            stddev-population, variance, variance-population, correlation,
            covariance or covariance-population). Use ml.rest.values for plugins.
        query : SearchQuery | str | None, default None
            Restrict the aggregated values to documents matching a structured,
            CTS or string query; None aggregates the whole lexicon.
        direction : {'ascending', 'descending'} | None, default None
            Lexicon order deciding which values limit and pos select.
        frequency : {'item', 'fragment'} | None, default None
            Count occurrences (item) or matching fragments (fragment).
        limit : int | None, default None
            Cap the lexicon subset before applying pos; None has no cap.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range of values to
            aggregate. None aggregates every value.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue | None
            The result converted to the function's native result type, or
            None when no values match.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        WrongParametersError
            If the name is blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope, lexicon=True)
        resp = self._rest.values.post(
            name,
            **params,
            data_format="json",
            view="aggregate",
            aggregate=function,
            direction=direction,
            frequency=frequency,
            limit=limit,
            timeout=timeout,
        )
        return _parse_aggregate(resp, function)

    def tuples(
        self,
        name: str,
        query: SearchInput = None,
        *,
        direction: Direction | None = None,
        frequency: Frequency | None = None,
        limit: int | None = None,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[TupleHit]:
        """Return typed co-occurring values of a named tuples definition.

        Sends POST with named or inline options. XML responses
        retain exact decimal tuple values; REST JSON tuples round them on the
        server. The tuples definition must exist in the scope's options or the
        server's default options.

        Parameters
        ----------
        name : str
            The name of a tuples definition in the query options.
        query : SearchQuery | str | None, default None
            Restrict co-occurrences to documents matching a structured, CTS or
            string query; None reads the whole lexicon.
        direction : {'ascending', 'descending'} | None, default None
            Lexicon order; None uses the options' sort order.
        frequency : {'item', 'fragment'} | None, default None
            Count occurrences (item) or matching fragments (fragment).
        limit : int | None, default None
            Cap the lexicon subset before applying pos; None has no cap.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range of tuples.
            None returns every tuple, as the endpoint does.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[TupleHit]
            Tuple components converted from their individual XML Schema types,
            with frequencies; [] when there are none.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, a query value has no local
            native form, or the name refers to a values definition.
        WrongParametersError
            If the name is blank, or direction or frequency is outside its
            supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope, lexicon=True)
        resp = self._rest.values.post(
            name,
            **params,
            data_format="xml",
            view="values",
            direction=direction,
            frequency=frequency,
            limit=limit,
            timeout=timeout,
        )
        return _parse_tuples(resp)

    def report(
        self,
        query: SearchInput = None,
        *,
        pos: PositionInput = None,
        view: ReportView = "all",
        transform: str | None = None,
        transform_params: dict | None = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> SearchReport:
        """Return a search report with results, scores, facets and metrics.

        Requests a normal JSON search response, not a multi-document read.
        Result snippets and extracts are not whole Document objects.

        Parameters
        ----------
        query : SearchQuery | str | None, default None
            A structured or CTS query, a string query, or None to match all.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range. None returns
            the first page: the options' page-length, 10 by default.
        view : {'all', 'results', 'facets', 'metadata'}, default 'all'
            Report sections requested from MarkLogic.
        transform : str | None, default None
            Installed REST response transform applied to the search report.
        transform_params : dict | None, default None
            Named parameters passed to the installed transform.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        SearchReport
            Parsed native report and effective snapshot timestamp. Total is
            an estimate; native result members include URI, score and snippets.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        WrongParametersError
            If the view is outside the supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope)
        resp = self._rest.search.post(
            **params,
            view=view,
            data_format="json",
            transform=transform,
            transform_params=transform_params,
            timeout=timeout,
        )
        return _parse_report(resp)


class AsyncSearchService:
    """Search documents, URIs and lexicon values through the async REST Search API.

    Queries are sent as JSON: structured queries as ``{"query": ...}``, CTS
    queries as ``{"ctsquery": ...}``, a string as a Search API string query.
    No XQuery is evaluated, so the REST user needs only the rest-reader role;
    a scope naming another database also needs the xdmp-eval-in privilege.

    The service carries a SearchScope: calling it, as in
    ``ml.search(database="catalog")``, returns a service whose operations all
    use that scope, and an operation's ``scope`` argument overrides it for one
    request.
    """

    def __init__(self, rest: AsyncRestApi, scope: SearchScope | None = None):
        """Create the service using the client's REST API.

        Parameters
        ----------
        rest : AsyncRestApi
            REST API used to send requests; no request is made here.
        scope : SearchScope | None, default None
            Scope applied to every operation; None searches the REST server's
            database without restrictions or options.
        """
        self._rest = rest
        self._scope = scope if scope is not None else SearchScope()

    def __call__(
        self,
        *,
        database: str | None = UNSET,
        txid: str | None = UNSET,
        collection: str | list[str] | None = UNSET,
        directory: str | None = UNSET,
        forest_name: str | list[str] | None = UNSET,
        options: OptionsInput = UNSET,
        timestamp: str | None = UNSET,
    ) -> AsyncSearchService:
        """Return a service whose operations use a narrower scope.

        Sends no request. Arguments override this service's scope field by
        field; omitted arguments are inherited and None clears an inherited
        value. A TransactionService unpacks into it: ``ml.search(**txn)``.

        Parameters
        ----------
        database : str | None, default unset
            Content database name or id; None uses the REST server's database.
        txid : str | None, default unset
            Multi-statement transaction to search within.
        collection : str | list[str] | None, default unset
            Restrict matches to one or more OR-related collections.
        directory : str | None, default unset
            Restrict matches to this database directory.
        forest_name : str | list[str] | None, default unset
            Restrict matches to these database forests.
        options : str | dict | SearchOptions | None, default unset
            Installed options name, or inline options members or builder.
        timestamp : str | None, default unset
            Effective timestamp from an earlier response, for snapshot
            pagination.

        Returns
        -------
        AsyncSearchService
            A new service bound to the same connection; this one is unchanged.
        """
        narrower = SearchScope(
            database=database,
            txid=txid,
            collection=collection,
            directory=directory,
            forest_name=forest_name,
            options=options,
            timestamp=timestamp,
        )
        return AsyncSearchService(self._rest, self._scope.overridden_by(narrower))

    @property
    def scope(self) -> SearchScope:
        """The scope applied to every operation of this service.

        Returns
        -------
        SearchScope
            An immutable scope; fields left unset are not sent.
        """
        return self._scope

    async def documents(
        self,
        query: SearchInput = None,
        *,
        pos: PositionInput = None,
        category: Category | str | list[Category | str] | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[Document]:
        """Return documents matching a query, in search result order.

        Sends a multi-document read (GET /v1/search, multipart/mixed, or POST
        with inline options). MarkLogic returns only the documents: no search
        report, snippets or facets.

        Parameters
        ----------
        query : SearchQuery | str | None, default None
            A structured or CTS query, a string query, or None to match all.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range. None returns
            the first page: the page-length of inline options, else 10.
            Installed options' page-length does not apply to this read.
        category : Category | str | list[Category | str] | None, default None
            Document data to return: content (default) and/or metadata categories.
        transform : str | None, default None
            Installed REST response transform applied to the document content.
        transform_params : dict | None, default None
            Named parameters passed to the installed transform.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[Document]
            Matching documents; [] when nothing matches.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        WrongParametersError
            If a category is outside the supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        category = normalize_category(category)
        params = _request_params(self._scope, query, pos, scope)
        resp = await self._rest.search.post(
            **params,
            category=category,
            data_format="json",
            transform=transform,
            transform_params=transform_params,
            multipart=True,
            timeout=timeout,
        )
        return _parse_documents(resp, category)

    async def uris(
        self,
        query: SearchInput = None,
        *,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[str]:
        """Return URIs of documents matching a query, in search result order.

        Sends a multi-document read of the smallest metadata category (quality)
        and takes each URI from its part's Content-Disposition, so no document
        content or search report is transferred.

        Parameters
        ----------
        query : SearchQuery | str | None, default None
            A structured or CTS query, a string query, or None to match all.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range. None returns
            the first page: the page-length of inline options, else 10.
            Installed options' page-length does not apply to this read.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[str]
            Matching document URIs; [] when nothing matches.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope)
        resp = await self._rest.search.post(
            **params,
            category=Category.QUALITY.value,
            data_format="json",
            multipart=True,
            timeout=timeout,
        )
        return _parse_uris(resp)

    async def values(
        self,
        name: str,
        query: SearchInput = None,
        *,
        direction: Direction | None = None,
        frequency: Frequency | None = None,
        limit: int | None = None,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[ValueHit]:
        """Return values of a named lexicon definition with their frequencies.

        Sends POST with named or inline options. The values
        definition must exist in the scope's options or the server's default
        options.

        Parameters
        ----------
        name : str
            The name of a values definition in the query options.
        query : SearchQuery | str | None, default None
            Restrict values to documents matching a structured, CTS or string
            query; None reads the whole lexicon.
        direction : {'ascending', 'descending'} | None, default None
            Lexicon order; None uses the options' sort order.
        frequency : {'item', 'fragment'} | None, default None
            Count occurrences (item) or matching fragments (fragment).
        limit : int | None, default None
            Cap the lexicon subset before applying pos; None has no cap.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range of values.
            None returns every value, as the endpoint does.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[ValueHit]
            Values converted from their reported XML Schema type, in lexicon
            order, with their frequencies; [] when there are none.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, a query value has no local
            native form, or the name refers to a tuples definition.
        WrongParametersError
            If the name is blank, or direction or frequency is outside its
            supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope, lexicon=True)
        resp = await self._rest.values.post(
            name,
            **params,
            data_format="json",
            view="values",
            direction=direction,
            frequency=frequency,
            limit=limit,
            timeout=timeout,
        )
        return _parse_values(resp)

    async def aggregate(
        self,
        name: str,
        function: AggregateFunction,
        query: SearchInput = None,
        *,
        direction: Direction | None = None,
        frequency: Frequency | None = None,
        limit: int | None = None,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> ParsedValue | None:
        """Apply a built-in aggregate to a values or tuples definition.

        Sends POST with named or inline options. The definition
        must exist in the scope's options or the server's default options.

        Parameters
        ----------
        name : str
            The name of a values or tuples definition in the query options.
        function : str
            Built-in aggregate (sum, avg, count, min, max, median, stddev,
            stddev-population, variance, variance-population, correlation,
            covariance or covariance-population). Use ml.rest.values for plugins.
        query : SearchQuery | str | None, default None
            Restrict the aggregated values to documents matching a structured,
            CTS or string query; None aggregates the whole lexicon.
        direction : {'ascending', 'descending'} | None, default None
            Lexicon order deciding which values limit and pos select.
        frequency : {'item', 'fragment'} | None, default None
            Count occurrences (item) or matching fragments (fragment).
        limit : int | None, default None
            Cap the lexicon subset before applying pos; None has no cap.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range of values to
            aggregate. None aggregates every value.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        ParsedValue | None
            The result converted to the function's native result type, or
            None when no values match.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        WrongParametersError
            If the name is blank.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope, lexicon=True)
        resp = await self._rest.values.post(
            name,
            **params,
            data_format="json",
            view="aggregate",
            aggregate=function,
            direction=direction,
            frequency=frequency,
            limit=limit,
            timeout=timeout,
        )
        return _parse_aggregate(resp, function)

    async def tuples(
        self,
        name: str,
        query: SearchInput = None,
        *,
        direction: Direction | None = None,
        frequency: Frequency | None = None,
        limit: int | None = None,
        pos: PositionInput = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> list[TupleHit]:
        """Return typed co-occurring values of a named tuples definition.

        Sends POST with named or inline options. XML responses
        retain exact decimal tuple values; REST JSON tuples round them on the
        server. The tuples definition must exist in the scope's options or the
        server's default options.

        Parameters
        ----------
        name : str
            The name of a tuples definition in the query options.
        query : SearchQuery | str | None, default None
            Restrict co-occurrences to documents matching a structured, CTS or
            string query; None reads the whole lexicon.
        direction : {'ascending', 'descending'} | None, default None
            Lexicon order; None uses the options' sort order.
        frequency : {'item', 'fragment'} | None, default None
            Count occurrences (item) or matching fragments (fragment).
        limit : int | None, default None
            Cap the lexicon subset before applying pos; None has no cap.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range of tuples.
            None returns every tuple, as the endpoint does.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        list[TupleHit]
            Tuple components converted from their individual XML Schema types,
            with frequencies; [] when there are none.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, a query value has no local
            native form, or the name refers to a values definition.
        WrongParametersError
            If the name is blank, or direction or frequency is outside its
            supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope, lexicon=True)
        resp = await self._rest.values.post(
            name,
            **params,
            data_format="xml",
            view="values",
            direction=direction,
            frequency=frequency,
            limit=limit,
            timeout=timeout,
        )
        return _parse_tuples(resp)

    async def report(
        self,
        query: SearchInput = None,
        *,
        pos: PositionInput = None,
        view: ReportView = "all",
        transform: str | None = None,
        transform_params: dict | None = None,
        scope: SearchScope | None = None,
        timeout=UNSET,
    ) -> SearchReport:
        """Return a search report with results, scores, facets and metrics.

        Requests a normal JSON search response, not a multi-document read.
        Result snippets and extracts are not whole Document objects.

        Parameters
        ----------
        query : SearchQuery | str | None, default None
            A structured or CTS query, a string query, or None to match all.
        pos : int | list[int] | tuple[int, int] | None, default None
            A one-based position or an inclusive [start, end] range. None returns
            the first page: the options' page-length, 10 by default.
        view : {'all', 'results', 'facets', 'metadata'}, default 'all'
            Report sections requested from MarkLogic.
        transform : str | None, default None
            Installed REST response transform applied to the search report.
        transform_params : dict | None, default None
            Named parameters passed to the installed transform.
        scope : SearchScope | None, default None
            Overrides the fields it sets on this service's scope for this request.
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout. Unset uses the client's configured
            timeout; None disables every HTTP timeout; a number sets all four
            components to that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        SearchReport
            Parsed native report and effective snapshot timestamp. Total is
            an estimate; native result members include URI, score and snippets.

        Raises
        ------
        TypeError
            If the query has an unsupported type or needs server evaluation, pos
            is not an integer or a two-item range of integers, or scope is not a
            SearchScope.
        ValueError
            If pos is not positive or not ordered, or a query value has no
            local native form.
        WrongParametersError
            If the view is outside the supported set.
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error.
        """
        params = _request_params(self._scope, query, pos, scope)
        resp = await self._rest.search.post(
            **params,
            view=view,
            data_format="json",
            transform=transform,
            transform_params=transform_params,
            timeout=timeout,
        )
        return _parse_report(resp)


def _request_params(
    service_scope: SearchScope,
    query: SearchInput,
    pos: PositionInput,
    scope: SearchScope | None,
    *,
    lexicon: bool = False,
) -> dict:
    """Build the combined-query POST arguments with their scope and paging.

    The query always travels in the body: in a GET URL a large query, such
    as a document query of a thousand URIs, exceeds the URL length limit.

    Parameters
    ----------
    service_scope : SearchScope
        Scope of the service sending the request.
    query : SearchQuery | str | None
        Search criteria, serialized locally.
    pos : int | list[int] | tuple[int, int] | None
        Requested positions.
    scope : SearchScope | None
        Per-request overrides of the service scope.
    lexicon : bool, default False
        Whether the request reads a lexicon through /v1/values.

    Returns
    -------
    dict
        The endpoint's post arguments: combined-query body, scope and paging.

    Raises
    ------
    TypeError
        If the query has an unsupported type.
    ValueError
        If pos is invalid.
    """
    effective = service_scope.overridden_by(scope)
    body, params = _criteria(query, effective.options, lexicon=lexicon)
    params.update(effective.request_params())
    if pos is None and not lexicon:
        params.update(_inline_page_length(body))
    params.update(_page_params(pos))
    return {"body": body, **params}


def _criteria(
    query: SearchInput,
    options: OptionsInput,
    *,
    lexicon: bool = False,
) -> tuple[dict, dict]:
    """Carry a query and options in a combined-query body.

    Installed options are named by the options URL parameter, which MarkLogic
    merges with any options in the body.

    Parameters
    ----------
    query : SearchQuery | str | None
        Search criteria, serialized locally.
    options : str | dict | SearchOptions | None
        Installed name, inline options members or builder, or unset.
    lexicon : bool, default False
        Use additional-query for inline CTS restrictions: ML10/ML12 ignore
        the combined body's ctsquery member on the values endpoint.

    Returns
    -------
    tuple[dict, dict]
        The combined-query body and the URL parameters.

    Raises
    ------
    TypeError
        If the query has an unsupported type.
    """
    params = {}
    inline: dict = {}
    if isinstance(options, str):
        params["options"] = options
    elif isinstance(options, SearchOptions):
        inline = options.to_json()["options"]
    elif isinstance(options, dict):
        inline = options
    return {"search": _combined_search(query, inline, lexicon=lexicon)}, params


def _combined_search(
    query: SearchInput,
    options: dict,
    *,
    lexicon: bool,
) -> dict:
    """Build the inner member of a combined query.

    Parameters
    ----------
    query : SearchQuery | str | None
        Search criteria, serialized locally.
    options : dict
        Native inline options members; empty when there are none.
    lexicon : bool
        Whether the combined query is sent to the values endpoint.

    Returns
    -------
    dict
        The ``search`` member: the serialized query or ``qtext``, and options.

    Raises
    ------
    TypeError
        If the query has an unsupported type, or a lexicon request's existing
        additional-query option is neither an XML string nor a list of them.
    """
    if query is None:
        return _with_options({}, options)
    if isinstance(query, str):
        return _with_options({"qtext": query}, options)
    if not isinstance(query, SearchQuery):
        message = "query must be a SearchQuery, a string query or None"
        raise TypeError(message)
    search = query.to_combined_query()["search"]
    if lexicon and "ctsquery" in search:
        # Values POST ignores combined ctsquery on ML10/ML12. The native
        # additional-query option accepts CTS XML strings in JSON options.
        return {"options": _with_additional_query(options, query)}
    return _with_options(search, options)


def _with_options(search: dict, options: dict) -> dict:
    """Add inline options to a combined query's search member when there are any.

    Parameters
    ----------
    search : dict
        The query or qtext member.
    options : dict
        Native inline options members.

    Returns
    -------
    dict
        The search member, with an options member only for non-empty options.
    """
    return {**search, "options": options} if options else search


def _inline_page_length(body: dict) -> dict:
    """Return the page length of inline options as an explicit URL parameter.

    A multi-document read ignores the page-length of inline options and
    returns 10 documents, so the service sends it as pageLength.

    Parameters
    ----------
    body : dict
        The combined-query body.

    Returns
    -------
    dict
        ``page_length`` when the inline options set page-length, else nothing.
    """
    page_length = body["search"].get("options", {}).get("page-length")
    return {} if page_length is None else {"page_length": page_length}


def _with_additional_query(options: dict, query: SearchQuery) -> dict:
    """AND a CTS query into the native additional-query option.

    Parameters
    ----------
    options : dict
        Native inline options members.
    query : SearchQuery
        A CTS query, serialized as XML.

    Returns
    -------
    dict
        A copy of the options whose additional-query list ends with the query.

    Raises
    ------
    TypeError
        If the existing additional-query is neither an XML string nor a list.
    """
    additional = options.get("additional-query", [])
    if isinstance(additional, str):
        additional = [additional]
    if not isinstance(additional, list):
        message = "additional-query must be an XML string or a list of XML strings"
        raise TypeError(message)
    serialized = ElementTree.tostring(query.to_xml(), encoding="unicode")
    return {**options, "additional-query": [*additional, serialized]}


def _page_params(pos: PositionInput) -> dict:
    """Return start and page length URL parameters selecting one-based positions.

    Parameters
    ----------
    pos : int | list[int] | tuple[int, int] | None
        A position, an inclusive [start, end] range, or None.

    Returns
    -------
    dict
        ``start`` and ``page_length``, or nothing for None.

    Raises
    ------
    TypeError
        If pos is neither an integer nor a two-item list or tuple of integers.
    ValueError
        If a position is not positive or the range end precedes its start.
    """
    if pos is None:
        return {}
    if isinstance(pos, (list, tuple)):
        if len(pos) != _RANGE_BOUND_COUNT:
            message = "pos ranges must contain exactly two positions"
            raise TypeError(message)
        start, end = pos
    else:
        start = end = pos
    if type(start) is not int or type(end) is not int:
        message = "pos positions must be integers"
        raise TypeError(message)
    if not 1 <= start <= end:
        message = "pos must satisfy 1 <= start <= end"
        raise ValueError(message)
    return {"start": start, "page_length": end - start + 1}


def _parse_documents(
    resp: Response,
    category: str | list[str] | None,
) -> list[Document]:
    """Parse a multi-document read into Document models.

    Parameters
    ----------
    resp : Response
        A multipart/mixed /v1/search response.
    category : str | list[str] | None
        Requested categories, selecting how parts combine into documents.

    Returns
    -------
    list[Document]
        Documents in response order; [] for an empty response.

    Raises
    ------
    MarkLogicError
        If MarkLogic returned an error.
    """
    MLResponseParser.raise_for_status(resp)
    if not resp.content:
        return []
    return list(DocumentsReader.parse(resp, category))


def _parse_uris(resp: Response) -> list[str]:
    """Return the document URIs named by the parts of a multi-document read.

    Parameters
    ----------
    resp : Response
        A multipart/mixed /v1/search response with one metadata part per document.
        A single part is parsed to one (headers, body) pair rather than a list.

    Returns
    -------
    list[str]
        URIs in response order; [] for an empty response.

    Raises
    ------
    MarkLogicError
        If MarkLogic returned an error.
    """
    MLResponseParser.raise_for_status(resp)
    if not resp.content:
        return []
    parts = MLResponseParser.parse_with_headers(resp, output_type=bytes)
    if not isinstance(parts, list):
        parts = [parts]
    return [
        DocumentsDisposition.from_header(
            headers.get(constants.HEADER_NAME_CONTENT_DISP),
        ).filename
        for headers, _ in parts
    ]


def _parse_values(resp: Response) -> list[ValueHit]:
    """Parse a JSON values response into typed ValueHit objects.

    Parameters
    ----------
    resp : Response
        A JSON /v1/values/{name} response.

    Returns
    -------
    list[ValueHit]
        Values in response order; [] when the response has none.

    Raises
    ------
    MarkLogicError
        If MarkLogic returned an error.
    ValueError
        If the response holds tuples rather than values.
    """
    MLResponseParser.raise_for_status(resp)
    values_response = resp.json()["values-response"]
    if "tuple" in values_response:
        message = "values() reads values definitions; use tuples() for co-occurrences"
        raise ValueError(message)
    atomic_type = values_response.get("type", "xs:string")
    return [
        ValueHit(
            MLResponseParser.parse_atomic(value["_value"], atomic_type),
            frequency=value["frequency"],
        )
        for value in values_response.get("distinct-value", [])
    ]


def _parse_tuples(resp: Response) -> list[TupleHit]:
    """Parse typed XML tuple components without REST JSON's decimal rounding.

    Parameters
    ----------
    resp : Response
        Native XML values response for a tuples definition.

    Returns
    -------
    list[TupleHit]
        Co-occurrences in response order, with exact lexical type conversion.

    Raises
    ------
    MarkLogicError
        If the server returned an error.
    ValueError
        If the response contains individual values rather than tuples.
    """
    MLResponseParser.raise_for_status(resp)
    payload = ElementTree.fromstring(resp.content)
    namespaces = {"search": SEARCH_NS_URI}
    if payload.find("search:distinct-value", namespaces) is not None:
        message = "tuples() reads tuples definitions; use values() for single values"
        raise ValueError(message)
    return [
        TupleHit(
            tuple(
                MLResponseParser.parse_atomic(
                    value.text or "",
                    value.attrib["{http://www.w3.org/2001/XMLSchema-instance}type"],
                )
                for value in item.findall("search:distinct-value", namespaces)
            ),
            frequency=int(item.attrib["frequency"]),
        )
        for item in payload.findall("search:tuple", namespaces)
    ]


def _parse_aggregate(
    resp: Response,
    function: str,
) -> ParsedValue | None:
    """Parse a built-in aggregate result with the type of the function's result.

    Parameters
    ----------
    resp : Response
        Native JSON aggregate response.
    function : str
        Requested aggregate function.

    Returns
    -------
    ParsedValue | None
        The typed result, or None when the lexicon holds no values to aggregate.

    Raises
    ------
    MarkLogicError
        If the server returned an error.
    """
    MLResponseParser.raise_for_status(resp)
    payload = resp.json()["values-response"]
    atomic_type = _aggregate_result_type(function, payload.get("type", "xs:string"))
    for result in payload.get("aggregate-result", []):
        if "_value" in result:
            return MLResponseParser.parse_atomic(result["_value"], atomic_type)
    return None


def _aggregate_result_type(function: str, lexicon_type: str) -> str:
    """Return the XML Schema type of a built-in aggregate's result.

    The values endpoint reports only the lexicon type, in JSON and XML alike,
    so the result type of functions that change it is derived here.

    Parameters
    ----------
    function : str
        Built-in aggregate function name.
    lexicon_type : str
        Type of the aggregated lexicon, such as ``xs:int``.

    Returns
    -------
    str
        The result type: integer for count, double for statistical functions,
        decimal for the average of an integer lexicon, else the lexicon type.
    """
    if function == "count":
        return "xs:integer"
    if function in _DOUBLE_AGGREGATES:
        return "xs:double"
    if function == "avg" and lexicon_type in _INTEGER_LEXICON_TYPES:
        return "xs:decimal"
    return lexicon_type


def _parse_report(resp: Response) -> SearchReport:
    """Retain the native JSON report and expose its common result sections.

    Parameters
    ----------
    resp : Response
        Native JSON search report.

    Returns
    -------
    SearchReport
        Parsed report including effective timestamp and unmodified extra fields.

    Raises
    ------
    MarkLogicError
        If the server returned an error.
    """
    MLResponseParser.raise_for_status(resp)
    payload = resp.json()
    return SearchReport(
        total=payload.get("total", 0),
        start=payload.get("start", 1),
        page_length=payload.get("page-length", 0),
        results=payload.get("results", []),
        facets=payload.get("facets", {}),
        metrics=payload.get("metrics", {}),
        effective_timestamp=resp.headers.get("ML-Effective-Timestamp"),
        response=payload,
    )
