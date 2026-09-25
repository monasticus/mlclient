"""Higher-level cts service (CtsService / AsyncCtsService).

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Headers

from mlclient._experimental import experimental
from mlclient._options import UNSET
from mlclient.functions.xqy import (
    Cts,
    XqyCompilationContext,
    XqyExpression,
    namespace_bindings,
)
from mlclient.models.results import SearchHit, ValueHit
from mlclient.multipart import decode_multipart_mixed
from mlclient.responses import MLResponseParser
from mlclient.services.eval import AsyncEvalService, EvalService

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi

Range = (
    int | list[int | XqyExpression] | tuple[int | XqyExpression, int | XqyExpression]
)
_RANGE_BOUND_COUNT = 2


class _CurrentHit(XqyExpression):
    """Reference the locally bound search hit in a service transport expression."""

    def render(self, _ctx: XqyCompilationContext) -> str:
        """Return the service-local variable; it contains no user-supplied text."""
        return "$_mlclient_hit"


class _ResultPairs(XqyExpression):
    """Pair each selected result with its native score or frequency."""

    def __init__(self, inner: XqyExpression, model: type, xpath: str | None = None):
        """Retain the selected expression and validate optional node projection.

        Parameters
        ----------
        inner : XqyExpression
            Native expression after index/range selection.
        model : type
            SearchHit or ValueHit determines score versus frequency extraction.
        xpath : str | None
            Optional validated projection applied to original search hits.
        """
        self.inner = inner
        self.measure = "score" if model is SearchHit else "frequency"
        item = _CurrentHit()
        self.projected = item if xpath is None else item.project(xpath)

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render pairs with the measure captured before node projection.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Shared external bindings and extraction-path validation.

        Returns
        -------
        str
            One XQuery sequence containing a payload and integer per result.
        """
        pairs = (
            f"let $_mlclient_measure := cts:{self.measure}($_mlclient_hit) "
            f"return (for $_mlclient_node in ({self.projected.render(ctx)}) "
            "return ($_mlclient_node, $_mlclient_measure))"
        )
        if self.measure == "frequency":
            pairs = (
                "if ($_mlclient_hit instance of map:map) then "
                'fn:error(fn:QName("", "MLCLIENT-LEXICON-MAP"), '
                '"Map output is not a value sequence; use eval.expression(Cts...) ") '
                f"else ({pairs})"
            )
        return f"for $_mlclient_hit in ({self.inner.render(ctx)}) return ({pairs})"


def _result_pairs(response, model: type):
    """Parse payload/measure pairs once without losing singleton cardinality.

    Parameters
    ----------
    response : httpx.Response
        Eval response produced by the service's paired expression.
    model : type
        SearchHit or ValueHit to construct from each pair.

    Returns
    -------
    SearchHit | ValueHit | list
        Empty list, one object, or a list of objects, according to cardinality.

    Raises
    ------
    ValueError
        If a payload lacks an integer score/frequency partner.
    MarkLogicError
        If the response reports a recognized server failure.
    HTTPStatusError
        If the response reports another HTTP failure.
    """
    MLResponseParser.raise_for_status(response)
    if not response.content:
        return []
    parts = decode_multipart_mixed(response.content, response.headers["Content-Type"])
    if len(parts) % 2:
        message = "CTS response is missing a score/frequency partner"
        raise ValueError(message)
    results = []
    for payload, measure in zip(parts[::2], parts[1::2]):
        if Headers(measure.headers).get("X-Primitive") != "integer":
            message = "CTS score/frequency partner must be an integer"
            raise ValueError(message)
        content = MLResponseParser.parse_part(payload)
        parameters = {"content_bytes": payload.content, "encoding": payload.encoding}
        if model is SearchHit:
            headers = Headers(payload.headers)
            result = SearchHit(
                content,
                score=int(measure.text),
                source_uri=headers.get("X-URI"),
                source_path=headers.get("X-Path", "/"),
                **parameters,
            )
        else:
            result = ValueHit(
                content,
                frequency=int(measure.text),
                **parameters,
            )
        results.append(result)
    return results[0] if len(results) == 1 else results


def _ranged(
    expr: XqyExpression,
    value: Range | None,
    index: int | XqyExpression | None,
) -> XqyExpression:
    """Apply mutually exclusive server-side index or inclusive range."""
    if index is not None:
        if value is not None:
            message = "index and range are mutually exclusive"
            raise ValueError(message)
        return expr.index(index)
    if value is None:
        return expr
    if type(value) is int:
        return expr.range(1, value)
    if not isinstance(value, (list, tuple)) or len(value) != _RANGE_BOUND_COUNT:
        message = "range must be an integer or a pair of integer positions"
        raise TypeError(message)
    return expr.range(*value)


def _execution_options(default_namespaces: dict[str, str], options: dict) -> dict:
    """Merge per-call namespace overrides without changing service defaults.

    Parameters
    ----------
    default_namespaces : dict[str, str]
        Namespace declarations owned by the CTS service.
    options : dict
        Per-call evaluator options, optionally including namespaces.

    Returns
    -------
    dict
        Independent options with namespace overrides applied by prefix.
    """
    return {
        **options,
        "namespaces": {
            **default_namespaces,
            **namespace_bindings(options.get("namespaces")),
        },
    }


def _single(item):
    """Require the scalar result returned by the estimate convenience method."""
    if isinstance(item, list):
        message = "expected exactly one result item"
        raise TypeError(message)
    return item


@experimental(log_on_init=True)
class CtsService(Cts):
    """Executes cts search, lexicon and estimate queries via ``/v1/eval``."""

    def __init__(self, rest: RestApi, *, namespaces=None):
        """Create search utilities using the client's REST API.

        Parameters
        ----------
        rest : RestApi
            REST API used by the expression evaluator; no request is made here.
        namespaces : dict[str, str] | None
            Default XQuery namespace declarations, copied at construction. The
            empty prefix sets the default element namespace. All execution
            methods accept namespaces overrides through keyword arguments.
        """
        self._namespaces = namespace_bindings(namespaces)
        self._eval = EvalService(rest)
        self._rest = rest

    def _execute(
        self,
        expr,
        model,
        *,
        namespaces=None,
        database=None,
        txid=None,
        timeout=UNSET,
    ):
        """Execute a service transport expression and decode its paired results.

        Parameters
        ----------
        expr : XqyExpression
            Service expression producing payload/integer pairs.
        model : type
            SearchHit or ValueHit.
        namespaces : dict | None
            Effective namespace declarations for path validation and execution.
        database : str | None
            Target database.
        txid : str | None
            Existing transaction identifier.
        timeout : object
            HTTP timeout override; UNSET inherits the client configuration.

        Returns
        -------
        SearchHit | ValueHit | list
            Results preserving empty/singleton/list cardinality.

        Raises
        ------
        ValueError
            If the returned result pairs are malformed.
        MarkLogicError
            If MarkLogic rejects the evaluation.
        HTTPStatusError
            If another HTTP failure occurs.
        """
        code, variables = expr.compile(namespaces=namespaces)
        response = self._rest.eval.post(
            xquery=code,
            variables=variables,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        return _result_pairs(response, model)

    def search(
        self,
        expression: str | XqyExpression | None = None,
        query: XqyExpression | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,
        index: int | XqyExpression | None = None,
        xpath: str | None = None,
        **kwargs,
    ) -> object:
        """Run ``cts:search`` and return parsed SearchHit objects.

        Parameters
        ----------
        expression : str | XqyExpression | None
            Searchable path string or composed expression; None uses /.
            Literal paths are validated before execution.
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | list | tuple | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns item or [].
        xpath : str | None
            Restricted extraction XPath applied to each hit after index/range.
            Relative paths start at the hit; absolute paths start at its root.
            Uses the same namespaces as expression and preserves hit order.
            None returns hits unchanged; one hit may yield zero or many nodes.
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.search(
                expression,
                query,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
            index,
        )
        return self._execute(
            _ResultPairs(expr, SearchHit, xpath),
            SearchHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def uris(
        self,
        *,
        start=None,
        options=None,
        query: XqyExpression | None = None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,
        index: int | XqyExpression | None = None,
        **kwargs,
    ) -> object:
        """Run ``cts:uris`` and return parsed ValueHit objects.

        Parameters
        ----------
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | list | tuple | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns item or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.uris(
                query=query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
            index,
        )
        return self._execute(
            _ResultPairs(expr, ValueHit),
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def values(
        self,
        range_indexes,
        *,
        start=None,
        options=None,
        query: XqyExpression | None = None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,
        index: int | XqyExpression | None = None,
        **kwargs,
    ) -> object:
        """Run ``cts:values`` and return parsed ValueHit objects.

        Parameters
        ----------
        range_indexes : XqyExpression | list | tuple
            One or more native range-index reference expressions.
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | list | tuple | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns item or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.values(
                range_indexes,
                query=query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
            index,
        )
        return self._execute(
            _ResultPairs(expr, ValueHit),
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def estimate(
        self,
        query: XqyExpression | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        maximum=None,
        **kwargs,
    ) -> int | str | bytes:
        """Run ``cts:estimate`` and return the fragment count.

        Parameters
        ----------
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        maximum : int | float | XqyExpression | None
            Native maximum count; None leaves the count uncapped.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        int
            The single native aggregate result (or raw str/bytes with output_type).

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        return _single(
            self._eval.expression(
                Cts.estimate(
                    query,
                    options=options,
                    quality_weight=quality_weight,
                    forest_ids=forest_ids,
                    maximum=maximum,
                ),
                **_execution_options(self._namespaces, kwargs),
            ),
        )

    def aggregate(
        self,
        native_plugin,
        aggregate_name,
        range_indexes,
        *,
        argument=None,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        native_plugin : xs:string
            The path to the native plugin library containing the implementation of
            the user-defined extension aggregate.
        aggregate_name : xs:string
            The name of an aggregate function in $native-plugin .
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        argument : item()*
            A sequence containing the arguments for the aggregate function.
        options : xs:string*
            options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.aggregate(...) to compose a nested expression.
        """
        expr = Cts.aggregate(
            native_plugin=native_plugin,
            aggregate_name=aggregate_name,
            range_indexes=range_indexes,
            argument=argument,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def avg_aggregate(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.avg_aggregate(...) to compose a nested expression.
        """
        expr = Cts.avg_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def classify(
        self,
        data_nodes,
        classifier,
        *,
        options=None,
        training_nodes=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        data_nodes : node()*
            The sequence of nodes to be classified.
        classifier : element(cts:classifier)
            An element node containing the classifier specification.
        options : (element()|map:map)?
            An options element .
        training_nodes : node()*
            The sequence of training nodes used to train the classifier.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.classify(...) to compose a nested expression.
        """
        expr = Cts.classify(
            data_nodes=data_nodes,
            classifier=classifier,
            options=options,
            training_nodes=training_nodes,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def cluster(self, nodes, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        nodes : node()*
            The sequence of nodes to cluster.
        options : (element()|map:map)?
            An XML representation of the options for defining the clustering
            parameters.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.cluster(...) to compose a nested expression.
        """
        expr = Cts.cluster(nodes=nodes, options=options)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def collection_match(
        self,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.collection_match(...) to compose a nested expression.
        """
        expr = Cts.collection_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def collections(
        self,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        start : xs:string?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.collections(...) to compose a nested expression.
        """
        expr = Cts.collections(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def confidence(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.confidence(...) to compose a nested expression.
        """
        expr = Cts.confidence(node=node)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def contains(self, nodes, query, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        nodes : item()*
            The nodes or atomic values to be checked for a match.
        query : cts:query
            A query to match against.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.contains(...) to compose a nested expression.
        """
        expr = Cts.contains(nodes=nodes, query=query)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def correlation(
        self,
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index.
        value2 : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.correlation(...) to compose a nested expression.
        """
        expr = Cts.correlation(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def count_aggregate(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.count_aggregate(...) to compose a nested expression.
        """
        expr = Cts.count_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def covariance(
        self,
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index.
        value2 : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.covariance(...) to compose a nested expression.
        """
        expr = Cts.covariance(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def covariance_p(
        self,
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index.
        value2 : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.covariance_p(...) to compose a nested expression.
        """
        expr = Cts.covariance_p(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def deregister(self, id, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        id : xs:unsignedLong
            A registered query identifier.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.deregister(...) to compose a nested expression.
        """
        expr = Cts.deregister(id=id)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def distinctive_terms(self, nodes, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        nodes : node()*
            Some model nodes.
        options : element()?
            An XML representation of the options for defining which terms to
            generate and how to evaluate them.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.distinctive_terms(...) to compose a nested expression.
        """
        expr = Cts.distinctive_terms(nodes=nodes, options=options)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_pair_geospatial_boxes(
        self,
        parent_element_names,
        latitude_names,
        longitude_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more element QNames.
        longitude_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_pair_geospatial_boxes(...) to compose a nested
        expression.
        """
        expr = Cts.element_attribute_pair_geospatial_boxes(
            parent_element_names=parent_element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_pair_geospatial_value_match(
        self,
        element_names,
        latitude_names,
        longitude_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_pair_geospatial_value_match(...) to compose a
        nested expression.
        """
        expr = Cts.element_attribute_pair_geospatial_value_match(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_pair_geospatial_values(
        self,
        element_names,
        latitude_names,
        longitude_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_pair_geospatial_values(...) to compose a nested
        expression.
        """
        expr = Cts.element_attribute_pair_geospatial_values(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_value_co_occurrences(
        self,
        element_name_1,
        attribute_name_1,
        element_name_2,
        attribute_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            An element QName.
        attribute_name_1 : xs:QName?
            An attribute QName or empty sequence.
        element_name_2 : xs:QName
            An element QName.
        attribute_name_2 : xs:QName?
            An attribute QName or empty sequence.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_co_occurrences(...) to compose a nested
        expression.
        """
        expr = Cts.element_attribute_value_co_occurrences(
            element_name_1=element_name_1,
            attribute_name_1=attribute_name_1,
            element_name_2=element_name_2,
            attribute_name_2=attribute_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_value_geospatial_co_occurrences(
        self,
        element_name_1,
        attribute_name_1,
        geo_element_name,
        *,
        coord_child_name_1=None,
        coord_child_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            A QName identifying the parent element of the first lexicon.
        attribute_name_1 : xs:QName?
            A QName identifying an attribute of element-name-1 .
        geo_element_name : xs:QName
            A QName identifying the second lexicon, which must reference a
            geospatial lexicon.
        coord_child_name_1 : xs:QName?
            Native coord_child_name_1 argument; see
            Cts.element_attribute_value_geospatial_co_occurrences for option
            details.
        coord_child_name_2 : xs:QName?
            Native coord_child_name_2 argument; see
            Cts.element_attribute_value_geospatial_co_occurrences for option
            details.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_geospatial_co_occurrences(...) to compose a
        nested expression.
        """
        expr = Cts.element_attribute_value_geospatial_co_occurrences(
            element_name_1=element_name_1,
            attribute_name_1=attribute_name_1,
            geo_element_name=geo_element_name,
            coord_child_name_1=coord_child_name_1,
            coord_child_name_2=coord_child_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_value_match(
        self,
        element_names,
        attribute_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_match(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_value_match(
            element_names=element_names,
            attribute_names=attribute_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_value_ranges(
        self,
        element_names,
        attribute_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_ranges(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_value_ranges(
            element_names=element_names,
            attribute_names=attribute_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_values(
        self,
        element_names,
        attribute_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        start : xs:anyAtomicType?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_values(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_values(
            element_names=element_names,
            attribute_names=attribute_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_word_match(
        self,
        element_names,
        attribute_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_word_match(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_word_match(
            element_names=element_names,
            attribute_names=attribute_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_attribute_words(
        self,
        element_names,
        attribute_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_words(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_words(
            element_names=element_names,
            attribute_names=attribute_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_child_geospatial_boxes(
        self,
        parent_element_names,
        child_element_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        child_element_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_child_geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.element_child_geospatial_boxes(
            parent_element_names=parent_element_names,
            child_element_names=child_element_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_child_geospatial_value_match(
        self,
        element_names,
        child_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames identifying the parent element(s).
        child_names : xs:QName*
            One or more child element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_child_geospatial_value_match(...) to compose a nested
        expression.
        """
        expr = Cts.element_child_geospatial_value_match(
            element_names=element_names,
            child_names=child_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_child_geospatial_values(
        self,
        element_names,
        child_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        child_names : xs:QName*
            One or more child element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_child_geospatial_values(...) to compose a nested expression.
        """
        expr = Cts.element_child_geospatial_values(
            element_names=element_names,
            child_names=child_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_geospatial_boxes(
        self,
        element_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Use the following options to customize your lexicon query: "ascending"
            Boxes should be returned in ascending order.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.element_geospatial_boxes(
            element_names=element_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_geospatial_value_match(
        self,
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_geospatial_value_match(...) to compose a nested expression.
        """
        expr = Cts.element_geospatial_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_geospatial_values(
        self,
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_geospatial_values(...) to compose a nested expression.
        """
        expr = Cts.element_geospatial_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_pair_geospatial_boxes(
        self,
        parent_element_names,
        latitude_names,
        longitude_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more element QNames.
        longitude_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_pair_geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.element_pair_geospatial_boxes(
            parent_element_names=parent_element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_pair_geospatial_value_match(
        self,
        element_names,
        latitude_names,
        longitude_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_pair_geospatial_value_match(...) to compose a nested
        expression.
        """
        expr = Cts.element_pair_geospatial_value_match(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_pair_geospatial_values(
        self,
        element_names,
        latitude_names,
        longitude_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames identifying the parent element of the
            latitude and longitude elements.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_pair_geospatial_values(...) to compose a nested expression.
        """
        expr = Cts.element_pair_geospatial_values(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_value_co_occurrences(
        self,
        element_name_1,
        element_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            An element QName.
        element_name_2 : xs:QName
            An element QName.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.element_value_co_occurrences(
            element_name_1=element_name_1,
            element_name_2=element_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_value_geospatial_co_occurrences(
        self,
        element_name_1,
        geo_element_name,
        *,
        coord_child_name_1=None,
        coord_child_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            A QName identifying the first lexicon.
        geo_element_name : xs:QName
            A QName identifying the second lexicon.
        coord_child_name_1 : xs:QName?
            Native coord_child_name_1 argument; see
            Cts.element_value_geospatial_co_occurrences for option details.
        coord_child_name_2 : xs:QName?
            Native coord_child_name_2 argument; see
            Cts.element_value_geospatial_co_occurrences for option details.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_geospatial_co_occurrences(...) to compose a nested
        expression.
        """
        expr = Cts.element_value_geospatial_co_occurrences(
            element_name_1=element_name_1,
            geo_element_name=geo_element_name,
            coord_child_name_1=coord_child_name_1,
            coord_child_name_2=coord_child_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_value_match(
        self,
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_match(...) to compose a nested expression.
        """
        expr = Cts.element_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_value_ranges(
        self,
        element_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_ranges(...) to compose a nested expression.
        """
        expr = Cts.element_value_ranges(
            element_names=element_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_values(
        self,
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : xs:anyAtomicType?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_values(...) to compose a nested expression.
        """
        expr = Cts.element_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_walk(self, node, element, expr, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to run the walk over.
        element : xs:QName*
            The name of elements to replace.
        expr : item()*
            An expression with which to replace each match.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_walk(...) to compose a nested expression.
        """
        expr = Cts.element_walk(node=node, element=element, expr=expr)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_word_match(
        self,
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:string?
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_word_match(...) to compose a nested expression.
        """
        expr = Cts.element_word_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_words(
        self,
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_words(...) to compose a nested expression.
        """
        expr = Cts.element_words(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def entity_dictionary_get(self, uri, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        uri : xs:string
            URI of a previously saved entity dictionary.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.entity_dictionary_get(...) to compose a nested expression.
        """
        expr = Cts.entity_dictionary_get(uri=uri)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def entity_highlight(self, node, expr, *, dict=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to run entity highlight on.
        expr : item()*
            An expression with which to replace each match.
        dict : cts:entity-dictionary
            The entity dictionary to use for matching entities in the text of the
            input node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.entity_highlight(...) to compose a nested expression.
        """
        expr = Cts.entity_highlight(node=node, expr=expr, dict=dict)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def entity_walk(self, node, expr, *, dict=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to walk.
        expr : item()*
            An expression to evaluate for each match.
        dict : cts:entity-dictionary
            The entity dictionary to use for matching entities in the text of the
            input node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.entity_walk(...) to compose a nested expression.
        """
        expr = Cts.entity_walk(node=node, expr=expr, dict=dict)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def field_value_co_occurrences(
        self,
        field_name_1,
        field_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_name_1 : xs:string
            A string.
        field_name_2 : xs:string
            A string.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_value_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.field_value_co_occurrences(
            field_name_1=field_name_1,
            field_name_2=field_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def field_value_match(
        self,
        field_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_value_match(...) to compose a nested expression.
        """
        expr = Cts.field_value_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def field_value_ranges(
        self,
        field_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more element QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_value_ranges(...) to compose a nested expression.
        """
        expr = Cts.field_value_ranges(
            field_names=field_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def field_values(
        self,
        field_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        start : xs:anyAtomicType?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_values(...) to compose a nested expression.
        """
        expr = Cts.field_values(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def field_word_match(
        self,
        field_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_word_match(...) to compose a nested expression.
        """
        expr = Cts.field_word_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def field_words(
        self,
        field_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_words(...) to compose a nested expression.
        """
        expr = Cts.field_words(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def fitness(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.fitness(...) to compose a nested expression.
        """
        expr = Cts.fitness(node=node)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def frequency(self, value, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value : item()
            A value from a lexicon lookup function.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.frequency(...) to compose a nested expression.
        """
        expr = Cts.frequency(value=value)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def geospatial_boxes(
        self,
        geo_indexes,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        geo_indexes : cts:reference*
            A sequence of references to geospatial indexes.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.geospatial_boxes(
            geo_indexes=geo_indexes,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def geospatial_co_occurrences(
        self,
        geo_element_name_1,
        geo_element_name_2,
        *,
        child_1_name_1=None,
        child_1_name_2=None,
        child_2_name_1=None,
        child_2_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        geo_element_name_1 : xs:QName
            A QName identifying the first lexicon.
        child_1_name_1 : xs:QName?
            Native child_1_name_1 argument; see Cts.geospatial_co_occurrences for
            option details.
        child_1_name_2 : xs:QName?
            Native child_1_name_2 argument; see Cts.geospatial_co_occurrences for
            option details.
        geo_element_name_2 : xs:QName
            A QName identifying the first lexicon.
        child_2_name_1 : xs:QName?
            Native child_2_name_1 argument; see Cts.geospatial_co_occurrences for
            option details.
        child_2_name_2 : xs:QName?
            Native child_2_name_2 argument; see Cts.geospatial_co_occurrences for
            option details.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.geospatial_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.geospatial_co_occurrences(
            geo_element_name_1=geo_element_name_1,
            geo_element_name_2=geo_element_name_2,
            child_1_name_1=child_1_name_1,
            child_1_name_2=child_1_name_2,
            child_2_name_1=child_2_name_1,
            child_2_name_2=child_2_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def highlight(self, node, query, expr, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to highlight.
        query : cts:query
            A query specifying the text to highlight.
        expr : item()*
            An expression with which to replace each match.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.highlight(...) to compose a nested expression.
        """
        expr = Cts.highlight(node=node, query=query, expr=expr)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def json_property_word_match(
        self,
        property_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        property_names : xs:string*
            One or more property names.
        pattern : xs:string?
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.json_property_word_match(...) to compose a nested expression.
        """
        expr = Cts.json_property_word_match(
            property_names=property_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def json_property_words(
        self,
        property_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        property_names : xs:string*
            One or more property names.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.json_property_words(...) to compose a nested expression.
        """
        expr = Cts.json_property_words(
            property_names=property_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def linear_model(
        self,
        values,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        values : cts:reference*
            References to two range indexes.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.linear_model(...) to compose a nested expression.
        """
        expr = Cts.linear_model(
            values=values,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def match_regions(
        self,
        range_indexes,
        operation,
        regions,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            References to range indexes that store the string serialization of
            regions to match against.
        operation : xs:string
            The operation to test.
        regions : cts:region*
            One or more cts:region values to test against.
        options : xs:string*
            String options you can use to control the operation.
        query : cts:query?
            Limit the region comparison to documents that match this query.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search should be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.match_regions(...) to compose a nested expression.
        """
        expr = Cts.match_regions(
            range_indexes=range_indexes,
            operation=operation,
            regions=regions,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def max(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.max(...) to compose a nested expression.
        """
        expr = Cts.max(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def median(self, arg, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:double*
            The sequence of values.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.median(...) to compose a nested expression.
        """
        expr = Cts.median(arg=arg)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def min(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.min(...) to compose a nested expression.
        """
        expr = Cts.min(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def part_of_speech(self, token, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        token : cts:token
            A token, as returned from cts:tokenize .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.part_of_speech(...) to compose a nested expression.
        """
        expr = Cts.part_of_speech(token=token)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def percent_rank(self, arg, value, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values.
        value : xs:anyAtomicType
            The value to be "ranked".
        options : xs:string*
            Options.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.percent_rank(...) to compose a nested expression.
        """
        expr = Cts.percent_rank(arg=arg, value=value, options=options)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def percentile(self, arg, p, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:double*
            The sequence of values.
        p : xs:double*
            The sequence of percentage(s).
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.percentile(...) to compose a nested expression.
        """
        expr = Cts.percentile(arg=arg, p=p)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def period_compare(self, period_1, operator, period_2, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        period_1 : cts:period
            The first period to compare.
        operator : xs:string
            A comparison operator.
        period_2 : cts:period
            The second period to compare against the first.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.period_compare(...) to compose a nested expression.
        """
        expr = Cts.period_compare(
            period_1=period_1,
            operator=operator,
            period_2=period_2,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def quality(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.quality(...) to compose a nested expression.
        """
        expr = Cts.quality(node=node)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def rank(self, arg, value, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values.
        value : xs:anyAtomicType
            The value to be "ranked".
        options : xs:string*
            Options.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.rank(...) to compose a nested expression.
        """
        expr = Cts.rank(arg=arg, value=value, options=options)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def register(self, query, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        query : cts:query
            A query to register.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.register(...) to compose a nested expression.
        """
        expr = Cts.register(query=query)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def relevance_info(self, *, node=None, output_kind=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        output_kind : xs:string
            The output kind.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.relevance_info(...) to compose a nested expression.
        """
        expr = Cts.relevance_info(node=node, output_kind=output_kind)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def remainder(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.remainder(...) to compose a nested expression.
        """
        expr = Cts.remainder(node=node)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def score(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.score(...) to compose a nested expression.
        """
        expr = Cts.score(node=node)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def stddev(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.stddev(...) to compose a nested expression.
        """
        expr = Cts.stddev(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def stddev_p(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.stddev_p(...) to compose a nested expression.
        """
        expr = Cts.stddev_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def stem(self, text, *, language=None, part_of_speech=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        text : xs:string
            A word or phrase to stem.
        language : xs:string?
            A language to use for stemming.
        part_of_speech : xs:string?
            A part of speech to use for stemming.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.stem(...) to compose a nested expression.
        """
        expr = Cts.stem(text=text, language=language, part_of_speech=part_of_speech)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def sum_aggregate(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.sum_aggregate(...) to compose a nested expression.
        """
        expr = Cts.sum_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def thresholds(
        self,
        computed_labels,
        known_labels,
        *,
        recall_weight=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        computed_labels : element(cts:label)*
            A sequence of element nodes containing the labels from classification
            (the output from cts:classify ) for a set of documents.
        known_labels : element(cts:label)*
            A sequence of element nodes containing the known labels for the same set
            of documents.
        recall_weight : xs:double?
            The factor to use in the calculation of the F measure.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.thresholds(...) to compose a nested expression.
        """
        expr = Cts.thresholds(
            computed_labels=computed_labels,
            known_labels=known_labels,
            recall_weight=recall_weight,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def tokenize(self, text, *, language=None, field=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        text : xs:string
            A word or phrase to tokenize.
        language : xs:string?
            A language to use for tokenization.
        field : xs:string?
            A field to use for tokenization.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.tokenize(...) to compose a nested expression.
        """
        expr = Cts.tokenize(text=text, language=language, field=field)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def train(self, training_nodes, labels, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        training_nodes : node()*
            The sequence of training nodes.
        labels : element(cts:label)*
            A sequence of labels for the training nodes, in the order corresponding
            to the training nodes.
        options : (element()|map:map)?
            Options with which to customize this operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.train(...) to compose a nested expression.
        """
        expr = Cts.train(training_nodes=training_nodes, labels=labels, options=options)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def triple_value_statistics(
        self,
        *,
        values=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        values : xs:anyAtomicType*
            The values to look up.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.triple_value_statistics(...) to compose a nested expression.
        """
        expr = Cts.triple_value_statistics(values=values, forest_ids=forest_ids)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def triples(
        self,
        *,
        subject=None,
        predicate=None,
        object=None,
        operator=None,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        subject : xs:anyAtomicType*
            The subjects to look up.
        predicate : xs:anyAtomicType*
            The predicates to look up.
        object : xs:anyAtomicType*
            The objects to look up.
        operator : xs:string*
            If a single string is provided it is treated as the operator for the
            $object values.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.triples(...) to compose a nested expression.
        """
        expr = Cts.triples(
            subject=subject,
            predicate=predicate,
            object=object,
            operator=operator,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def uri_match(
        self,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.uri_match(...) to compose a nested expression.
        """
        expr = Cts.uri_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_document_patch_path(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_document_patch_path(...) to compose a nested expression.
        """
        expr = Cts.valid_document_patch_path(string=string, map=map)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_extract_path(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_extract_path(...) to compose a nested expression.
        """
        expr = Cts.valid_extract_path(string=string, map=map)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_index_path(self, string, ignorens, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        ignorens : xs:boolean
            Ignore namespace prefix binding errors.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_index_path(...) to compose a nested expression.
        """
        expr = Cts.valid_index_path(string=string, ignorens=ignorens)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_optic_path(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_optic_path(...) to compose a nested expression.
        """
        expr = Cts.valid_optic_path(string=string, map=map)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_tde_context(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_tde_context(...) to compose a nested expression.
        """
        expr = Cts.valid_tde_context(string=string, map=map)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def value_co_occurrences(
        self,
        range_index_1,
        range_index_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index_1 : cts:reference
            A reference to a range index.
        range_index_2 : cts:reference
            A reference to a range index.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.value_co_occurrences(
            range_index_1=range_index_1,
            range_index_2=range_index_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def value_match(
        self,
        range_indexes,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_match(...) to compose a nested expression.
        """
        expr = Cts.value_match(
            range_indexes=range_indexes,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def value_ranges(
        self,
        range_indexes,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_ranges(...) to compose a nested expression.
        """
        expr = Cts.value_ranges(
            range_indexes=range_indexes,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def value_tuples(
        self,
        range_indexes,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_tuples(...) to compose a nested expression.
        """
        expr = Cts.value_tuples(
            range_indexes=range_indexes,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def variance(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.variance(...) to compose a nested expression.
        """
        expr = Cts.variance(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def variance_p(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.variance_p(...) to compose a nested expression.
        """
        expr = Cts.variance_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def walk(self, node, query, expr, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to walk.
        query : cts:query
            A query specifying the text on which to evaluate the expression.
        expr : item()*
            An expression to evaluate with matching text.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.walk(...) to compose a nested expression.
        """
        expr = Cts.walk(node=node, query=query, expr=expr)
        return self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def word_match(
        self,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        pattern : xs:string
            A wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.word_match(...) to compose a nested expression.
        """
        expr = Cts.word_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def words(
        self,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.words(...) to compose a nested expression.
        """
        expr = Cts.words(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )


@experimental(log_on_init=True)
class AsyncCtsService(Cts):
    """Async execution of cts search, lexicon and estimate queries via ``/v1/eval``."""

    async def aggregate(
        self,
        native_plugin,
        aggregate_name,
        range_indexes,
        *,
        argument=None,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        native_plugin : xs:string
            The path to the native plugin library containing the implementation of
            the user-defined extension aggregate.
        aggregate_name : xs:string
            The name of an aggregate function in $native-plugin .
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        argument : item()*
            A sequence containing the arguments for the aggregate function.
        options : xs:string*
            options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.aggregate(...) to compose a nested expression.
        """
        expr = Cts.aggregate(
            native_plugin=native_plugin,
            aggregate_name=aggregate_name,
            range_indexes=range_indexes,
            argument=argument,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def avg_aggregate(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.avg_aggregate(...) to compose a nested expression.
        """
        expr = Cts.avg_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def classify(
        self,
        data_nodes,
        classifier,
        *,
        options=None,
        training_nodes=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        data_nodes : node()*
            The sequence of nodes to be classified.
        classifier : element(cts:classifier)
            An element node containing the classifier specification.
        options : (element()|map:map)?
            An options element .
        training_nodes : node()*
            The sequence of training nodes used to train the classifier.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.classify(...) to compose a nested expression.
        """
        expr = Cts.classify(
            data_nodes=data_nodes,
            classifier=classifier,
            options=options,
            training_nodes=training_nodes,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def cluster(self, nodes, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        nodes : node()*
            The sequence of nodes to cluster.
        options : (element()|map:map)?
            An XML representation of the options for defining the clustering
            parameters.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.cluster(...) to compose a nested expression.
        """
        expr = Cts.cluster(nodes=nodes, options=options)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def collection_match(
        self,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.collection_match(...) to compose a nested expression.
        """
        expr = Cts.collection_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def collections(
        self,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        start : xs:string?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.collections(...) to compose a nested expression.
        """
        expr = Cts.collections(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def confidence(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.confidence(...) to compose a nested expression.
        """
        expr = Cts.confidence(node=node)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def contains(self, nodes, query, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        nodes : item()*
            The nodes or atomic values to be checked for a match.
        query : cts:query
            A query to match against.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.contains(...) to compose a nested expression.
        """
        expr = Cts.contains(nodes=nodes, query=query)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def correlation(
        self,
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index.
        value2 : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.correlation(...) to compose a nested expression.
        """
        expr = Cts.correlation(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def count_aggregate(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.count_aggregate(...) to compose a nested expression.
        """
        expr = Cts.count_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def covariance(
        self,
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index.
        value2 : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.covariance(...) to compose a nested expression.
        """
        expr = Cts.covariance(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def covariance_p(
        self,
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index.
        value2 : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.covariance_p(...) to compose a nested expression.
        """
        expr = Cts.covariance_p(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def deregister(self, id, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        id : xs:unsignedLong
            A registered query identifier.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.deregister(...) to compose a nested expression.
        """
        expr = Cts.deregister(id=id)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def distinctive_terms(self, nodes, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        nodes : node()*
            Some model nodes.
        options : element()?
            An XML representation of the options for defining which terms to
            generate and how to evaluate them.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.distinctive_terms(...) to compose a nested expression.
        """
        expr = Cts.distinctive_terms(nodes=nodes, options=options)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_pair_geospatial_boxes(
        self,
        parent_element_names,
        latitude_names,
        longitude_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more element QNames.
        longitude_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_pair_geospatial_boxes(...) to compose a nested
        expression.
        """
        expr = Cts.element_attribute_pair_geospatial_boxes(
            parent_element_names=parent_element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_pair_geospatial_value_match(
        self,
        element_names,
        latitude_names,
        longitude_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_pair_geospatial_value_match(...) to compose a
        nested expression.
        """
        expr = Cts.element_attribute_pair_geospatial_value_match(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_pair_geospatial_values(
        self,
        element_names,
        latitude_names,
        longitude_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_pair_geospatial_values(...) to compose a nested
        expression.
        """
        expr = Cts.element_attribute_pair_geospatial_values(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_value_co_occurrences(
        self,
        element_name_1,
        attribute_name_1,
        element_name_2,
        attribute_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            An element QName.
        attribute_name_1 : xs:QName?
            An attribute QName or empty sequence.
        element_name_2 : xs:QName
            An element QName.
        attribute_name_2 : xs:QName?
            An attribute QName or empty sequence.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_co_occurrences(...) to compose a nested
        expression.
        """
        expr = Cts.element_attribute_value_co_occurrences(
            element_name_1=element_name_1,
            attribute_name_1=attribute_name_1,
            element_name_2=element_name_2,
            attribute_name_2=attribute_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_value_geospatial_co_occurrences(
        self,
        element_name_1,
        attribute_name_1,
        geo_element_name,
        *,
        coord_child_name_1=None,
        coord_child_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            A QName identifying the parent element of the first lexicon.
        attribute_name_1 : xs:QName?
            A QName identifying an attribute of element-name-1 .
        geo_element_name : xs:QName
            A QName identifying the second lexicon, which must reference a
            geospatial lexicon.
        coord_child_name_1 : xs:QName?
            Native coord_child_name_1 argument; see
            Cts.element_attribute_value_geospatial_co_occurrences for option
            details.
        coord_child_name_2 : xs:QName?
            Native coord_child_name_2 argument; see
            Cts.element_attribute_value_geospatial_co_occurrences for option
            details.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_geospatial_co_occurrences(...) to compose a
        nested expression.
        """
        expr = Cts.element_attribute_value_geospatial_co_occurrences(
            element_name_1=element_name_1,
            attribute_name_1=attribute_name_1,
            geo_element_name=geo_element_name,
            coord_child_name_1=coord_child_name_1,
            coord_child_name_2=coord_child_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_value_match(
        self,
        element_names,
        attribute_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_match(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_value_match(
            element_names=element_names,
            attribute_names=attribute_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_value_ranges(
        self,
        element_names,
        attribute_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_value_ranges(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_value_ranges(
            element_names=element_names,
            attribute_names=attribute_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_values(
        self,
        element_names,
        attribute_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        start : xs:anyAtomicType?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_values(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_values(
            element_names=element_names,
            attribute_names=attribute_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_word_match(
        self,
        element_names,
        attribute_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_word_match(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_word_match(
            element_names=element_names,
            attribute_names=attribute_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_attribute_words(
        self,
        element_names,
        attribute_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_attribute_words(...) to compose a nested expression.
        """
        expr = Cts.element_attribute_words(
            element_names=element_names,
            attribute_names=attribute_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_child_geospatial_boxes(
        self,
        parent_element_names,
        child_element_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        child_element_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_child_geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.element_child_geospatial_boxes(
            parent_element_names=parent_element_names,
            child_element_names=child_element_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_child_geospatial_value_match(
        self,
        element_names,
        child_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames identifying the parent element(s).
        child_names : xs:QName*
            One or more child element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_child_geospatial_value_match(...) to compose a nested
        expression.
        """
        expr = Cts.element_child_geospatial_value_match(
            element_names=element_names,
            child_names=child_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_child_geospatial_values(
        self,
        element_names,
        child_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        child_names : xs:QName*
            One or more child element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_child_geospatial_values(...) to compose a nested expression.
        """
        expr = Cts.element_child_geospatial_values(
            element_names=element_names,
            child_names=child_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_geospatial_boxes(
        self,
        element_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Use the following options to customize your lexicon query: "ascending"
            Boxes should be returned in ascending order.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.element_geospatial_boxes(
            element_names=element_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_geospatial_value_match(
        self,
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_geospatial_value_match(...) to compose a nested expression.
        """
        expr = Cts.element_geospatial_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_geospatial_values(
        self,
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_geospatial_values(...) to compose a nested expression.
        """
        expr = Cts.element_geospatial_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_pair_geospatial_boxes(
        self,
        parent_element_names,
        latitude_names,
        longitude_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more element QNames.
        longitude_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_pair_geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.element_pair_geospatial_boxes(
            parent_element_names=parent_element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_pair_geospatial_value_match(
        self,
        element_names,
        latitude_names,
        longitude_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_pair_geospatial_value_match(...) to compose a nested
        expression.
        """
        expr = Cts.element_pair_geospatial_value_match(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_pair_geospatial_values(
        self,
        element_names,
        latitude_names,
        longitude_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames identifying the parent element of the
            latitude and longitude elements.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        start : cts:point?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_pair_geospatial_values(...) to compose a nested expression.
        """
        expr = Cts.element_pair_geospatial_values(
            element_names=element_names,
            latitude_names=latitude_names,
            longitude_names=longitude_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_value_co_occurrences(
        self,
        element_name_1,
        element_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            An element QName.
        element_name_2 : xs:QName
            An element QName.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.element_value_co_occurrences(
            element_name_1=element_name_1,
            element_name_2=element_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_value_geospatial_co_occurrences(
        self,
        element_name_1,
        geo_element_name,
        *,
        coord_child_name_1=None,
        coord_child_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_name_1 : xs:QName
            A QName identifying the first lexicon.
        geo_element_name : xs:QName
            A QName identifying the second lexicon.
        coord_child_name_1 : xs:QName?
            Native coord_child_name_1 argument; see
            Cts.element_value_geospatial_co_occurrences for option details.
        coord_child_name_2 : xs:QName?
            Native coord_child_name_2 argument; see
            Cts.element_value_geospatial_co_occurrences for option details.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_geospatial_co_occurrences(...) to compose a nested
        expression.
        """
        expr = Cts.element_value_geospatial_co_occurrences(
            element_name_1=element_name_1,
            geo_element_name=geo_element_name,
            coord_child_name_1=coord_child_name_1,
            coord_child_name_2=coord_child_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_value_match(
        self,
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_match(...) to compose a nested expression.
        """
        expr = Cts.element_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_value_ranges(
        self,
        element_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_value_ranges(...) to compose a nested expression.
        """
        expr = Cts.element_value_ranges(
            element_names=element_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_values(
        self,
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : xs:anyAtomicType?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_values(...) to compose a nested expression.
        """
        expr = Cts.element_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_walk(self, node, element, expr, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to run the walk over.
        element : xs:QName*
            The name of elements to replace.
        expr : item()*
            An expression with which to replace each match.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_walk(...) to compose a nested expression.
        """
        expr = Cts.element_walk(node=node, element=element, expr=expr)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_word_match(
        self,
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:string?
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_word_match(...) to compose a nested expression.
        """
        expr = Cts.element_word_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_words(
        self,
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.element_words(...) to compose a nested expression.
        """
        expr = Cts.element_words(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def entity_dictionary_get(self, uri, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        uri : xs:string
            URI of a previously saved entity dictionary.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.entity_dictionary_get(...) to compose a nested expression.
        """
        expr = Cts.entity_dictionary_get(uri=uri)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def entity_highlight(self, node, expr, *, dict=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to run entity highlight on.
        expr : item()*
            An expression with which to replace each match.
        dict : cts:entity-dictionary
            The entity dictionary to use for matching entities in the text of the
            input node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.entity_highlight(...) to compose a nested expression.
        """
        expr = Cts.entity_highlight(node=node, expr=expr, dict=dict)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def entity_walk(self, node, expr, *, dict=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to walk.
        expr : item()*
            An expression to evaluate for each match.
        dict : cts:entity-dictionary
            The entity dictionary to use for matching entities in the text of the
            input node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.entity_walk(...) to compose a nested expression.
        """
        expr = Cts.entity_walk(node=node, expr=expr, dict=dict)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def field_value_co_occurrences(
        self,
        field_name_1,
        field_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_name_1 : xs:string
            A string.
        field_name_2 : xs:string
            A string.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_value_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.field_value_co_occurrences(
            field_name_1=field_name_1,
            field_name_2=field_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def field_value_match(
        self,
        field_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_value_match(...) to compose a nested expression.
        """
        expr = Cts.field_value_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def field_value_ranges(
        self,
        field_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more element QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_value_ranges(...) to compose a nested expression.
        """
        expr = Cts.field_value_ranges(
            field_names=field_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def field_values(
        self,
        field_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        start : xs:anyAtomicType?
            A starting value.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_values(...) to compose a nested expression.
        """
        expr = Cts.field_values(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def field_word_match(
        self,
        field_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_word_match(...) to compose a nested expression.
        """
        expr = Cts.field_word_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def field_words(
        self,
        field_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.field_words(...) to compose a nested expression.
        """
        expr = Cts.field_words(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def fitness(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.fitness(...) to compose a nested expression.
        """
        expr = Cts.fitness(node=node)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def frequency(self, value, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        value : item()
            A value from a lexicon lookup function.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.frequency(...) to compose a nested expression.
        """
        expr = Cts.frequency(value=value)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def geospatial_boxes(
        self,
        geo_indexes,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        geo_indexes : cts:reference*
            A sequence of references to geospatial indexes.
        latitude_bounds : xs:double*
            A sequence of latitude bounds.
        longitude_bounds : xs:double*
            A sequence of longitude bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.geospatial_boxes(...) to compose a nested expression.
        """
        expr = Cts.geospatial_boxes(
            geo_indexes=geo_indexes,
            latitude_bounds=latitude_bounds,
            longitude_bounds=longitude_bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def geospatial_co_occurrences(
        self,
        geo_element_name_1,
        geo_element_name_2,
        *,
        child_1_name_1=None,
        child_1_name_2=None,
        child_2_name_1=None,
        child_2_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        geo_element_name_1 : xs:QName
            A QName identifying the first lexicon.
        child_1_name_1 : xs:QName?
            Native child_1_name_1 argument; see Cts.geospatial_co_occurrences for
            option details.
        child_1_name_2 : xs:QName?
            Native child_1_name_2 argument; see Cts.geospatial_co_occurrences for
            option details.
        geo_element_name_2 : xs:QName
            A QName identifying the first lexicon.
        child_2_name_1 : xs:QName?
            Native child_2_name_1 argument; see Cts.geospatial_co_occurrences for
            option details.
        child_2_name_2 : xs:QName?
            Native child_2_name_2 argument; see Cts.geospatial_co_occurrences for
            option details.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.geospatial_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.geospatial_co_occurrences(
            geo_element_name_1=geo_element_name_1,
            geo_element_name_2=geo_element_name_2,
            child_1_name_1=child_1_name_1,
            child_1_name_2=child_1_name_2,
            child_2_name_1=child_2_name_1,
            child_2_name_2=child_2_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def highlight(self, node, query, expr, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to highlight.
        query : cts:query
            A query specifying the text to highlight.
        expr : item()*
            An expression with which to replace each match.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.highlight(...) to compose a nested expression.
        """
        expr = Cts.highlight(node=node, query=query, expr=expr)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def json_property_word_match(
        self,
        property_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        property_names : xs:string*
            One or more property names.
        pattern : xs:string?
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.json_property_word_match(...) to compose a nested expression.
        """
        expr = Cts.json_property_word_match(
            property_names=property_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def json_property_words(
        self,
        property_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        property_names : xs:string*
            One or more property names.
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.json_property_words(...) to compose a nested expression.
        """
        expr = Cts.json_property_words(
            property_names=property_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def linear_model(
        self,
        values,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        values : cts:reference*
            References to two range indexes.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.linear_model(...) to compose a nested expression.
        """
        expr = Cts.linear_model(
            values=values,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def match_regions(
        self,
        range_indexes,
        operation,
        regions,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            References to range indexes that store the string serialization of
            regions to match against.
        operation : xs:string
            The operation to test.
        regions : cts:region*
            One or more cts:region values to test against.
        options : xs:string*
            String options you can use to control the operation.
        query : cts:query?
            Limit the region comparison to documents that match this query.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search should be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.match_regions(...) to compose a nested expression.
        """
        expr = Cts.match_regions(
            range_indexes=range_indexes,
            operation=operation,
            regions=regions,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def max(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.max(...) to compose a nested expression.
        """
        expr = Cts.max(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def median(self, arg, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:double*
            The sequence of values.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.median(...) to compose a nested expression.
        """
        expr = Cts.median(arg=arg)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def min(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.min(...) to compose a nested expression.
        """
        expr = Cts.min(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def part_of_speech(self, token, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        token : cts:token
            A token, as returned from cts:tokenize .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.part_of_speech(...) to compose a nested expression.
        """
        expr = Cts.part_of_speech(token=token)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def percent_rank(self, arg, value, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values.
        value : xs:anyAtomicType
            The value to be "ranked".
        options : xs:string*
            Options.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.percent_rank(...) to compose a nested expression.
        """
        expr = Cts.percent_rank(arg=arg, value=value, options=options)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def percentile(self, arg, p, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:double*
            The sequence of values.
        p : xs:double*
            The sequence of percentage(s).
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.percentile(...) to compose a nested expression.
        """
        expr = Cts.percentile(arg=arg, p=p)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def period_compare(self, period_1, operator, period_2, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        period_1 : cts:period
            The first period to compare.
        operator : xs:string
            A comparison operator.
        period_2 : cts:period
            The second period to compare against the first.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.period_compare(...) to compose a nested expression.
        """
        expr = Cts.period_compare(
            period_1=period_1,
            operator=operator,
            period_2=period_2,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def quality(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.quality(...) to compose a nested expression.
        """
        expr = Cts.quality(node=node)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def rank(self, arg, value, *, options=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values.
        value : xs:anyAtomicType
            The value to be "ranked".
        options : xs:string*
            Options.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.rank(...) to compose a nested expression.
        """
        expr = Cts.rank(arg=arg, value=value, options=options)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def register(self, query, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        query : cts:query
            A query to register.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.register(...) to compose a nested expression.
        """
        expr = Cts.register(query=query)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def relevance_info(
        self,
        *,
        node=None,
        output_kind=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        output_kind : xs:string
            The output kind.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.relevance_info(...) to compose a nested expression.
        """
        expr = Cts.relevance_info(node=node, output_kind=output_kind)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def remainder(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.remainder(...) to compose a nested expression.
        """
        expr = Cts.remainder(node=node)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def score(self, *, node=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.score(...) to compose a nested expression.
        """
        expr = Cts.score(node=node)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def stddev(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.stddev(...) to compose a nested expression.
        """
        expr = Cts.stddev(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def stddev_p(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.stddev_p(...) to compose a nested expression.
        """
        expr = Cts.stddev_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def stem(
        self,
        text,
        *,
        language=None,
        part_of_speech=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        text : xs:string
            A word or phrase to stem.
        language : xs:string?
            A language to use for stemming.
        part_of_speech : xs:string?
            A part of speech to use for stemming.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.stem(...) to compose a nested expression.
        """
        expr = Cts.stem(text=text, language=language, part_of_speech=part_of_speech)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def sum_aggregate(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.sum_aggregate(...) to compose a nested expression.
        """
        expr = Cts.sum_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def thresholds(
        self,
        computed_labels,
        known_labels,
        *,
        recall_weight=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        computed_labels : element(cts:label)*
            A sequence of element nodes containing the labels from classification
            (the output from cts:classify ) for a set of documents.
        known_labels : element(cts:label)*
            A sequence of element nodes containing the known labels for the same set
            of documents.
        recall_weight : xs:double?
            The factor to use in the calculation of the F measure.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.thresholds(...) to compose a nested expression.
        """
        expr = Cts.thresholds(
            computed_labels=computed_labels,
            known_labels=known_labels,
            recall_weight=recall_weight,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def tokenize(self, text, *, language=None, field=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        text : xs:string
            A word or phrase to tokenize.
        language : xs:string?
            A language to use for tokenization.
        field : xs:string?
            A field to use for tokenization.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.tokenize(...) to compose a nested expression.
        """
        expr = Cts.tokenize(text=text, language=language, field=field)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def train(
        self,
        training_nodes,
        labels,
        *,
        options=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        training_nodes : node()*
            The sequence of training nodes.
        labels : element(cts:label)*
            A sequence of labels for the training nodes, in the order corresponding
            to the training nodes.
        options : (element()|map:map)?
            Options with which to customize this operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.train(...) to compose a nested expression.
        """
        expr = Cts.train(training_nodes=training_nodes, labels=labels, options=options)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def triple_value_statistics(
        self,
        *,
        values=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        values : xs:anyAtomicType*
            The values to look up.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.triple_value_statistics(...) to compose a nested expression.
        """
        expr = Cts.triple_value_statistics(values=values, forest_ids=forest_ids)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def triples(
        self,
        *,
        subject=None,
        predicate=None,
        object=None,
        operator=None,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        subject : xs:anyAtomicType*
            The subjects to look up.
        predicate : xs:anyAtomicType*
            The predicates to look up.
        object : xs:anyAtomicType*
            The objects to look up.
        operator : xs:string*
            If a single string is provided it is treated as the operator for the
            $object values.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.triples(...) to compose a nested expression.
        """
        expr = Cts.triples(
            subject=subject,
            predicate=predicate,
            object=object,
            operator=operator,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def uri_match(
        self,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.uri_match(...) to compose a nested expression.
        """
        expr = Cts.uri_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_document_patch_path(
        self,
        string,
        *,
        map=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_document_patch_path(...) to compose a nested expression.
        """
        expr = Cts.valid_document_patch_path(string=string, map=map)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_extract_path(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_extract_path(...) to compose a nested expression.
        """
        expr = Cts.valid_extract_path(string=string, map=map)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_index_path(self, string, ignorens, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        ignorens : xs:boolean
            Ignore namespace prefix binding errors.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_index_path(...) to compose a nested expression.
        """
        expr = Cts.valid_index_path(string=string, ignorens=ignorens)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_optic_path(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_optic_path(...) to compose a nested expression.
        """
        expr = Cts.valid_optic_path(string=string, map=map)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_tde_context(self, string, *, map=None, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.valid_tde_context(...) to compose a nested expression.
        """
        expr = Cts.valid_tde_context(string=string, map=map)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def value_co_occurrences(
        self,
        range_index_1,
        range_index_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index_1 : cts:reference
            A reference to a range index.
        range_index_2 : cts:reference
            A reference to a range index.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_co_occurrences(...) to compose a nested expression.
        """
        expr = Cts.value_co_occurrences(
            range_index_1=range_index_1,
            range_index_2=range_index_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def value_match(
        self,
        range_indexes,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        pattern : xs:anyAtomicType
            A pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_match(...) to compose a nested expression.
        """
        expr = Cts.value_match(
            range_indexes=range_indexes,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def value_ranges(
        self,
        range_indexes,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        bounds : xs:anyAtomicType*
            A sequence of range bounds.
        options : xs:string*
            Options.
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_ranges(...) to compose a nested expression.
        """
        expr = Cts.value_ranges(
            range_indexes=range_indexes,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def value_tuples(
        self,
        range_indexes,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        options : xs:string*
            Options.
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences.
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.value_tuples(...) to compose a nested expression.
        """
        expr = Cts.value_tuples(
            range_indexes=range_indexes,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def variance(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.variance(...) to compose a nested expression.
        """
        expr = Cts.variance(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def variance_p(
        self,
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.variance_p(...) to compose a nested expression.
        """
        expr = Cts.variance_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def walk(self, node, query, expr, **kwargs) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        node : node()
            A node to walk.
        query : cts:query
            A query specifying the text on which to evaluate the expression.
        expr : item()*
            An expression to evaluate with matching text.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        object | list
            Native parsed results; empty/singleton/list cardinality is preserved.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.walk(...) to compose a nested expression.
        """
        expr = Cts.walk(node=node, query=query, expr=expr)
        return await self._eval.expression(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def word_match(
        self,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        pattern : xs:string
            A wildcard pattern to match.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.word_match(...) to compose a nested expression.
        """
        expr = Cts.word_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def words(
        self,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
        range=None,
        index=None,
        **kwargs,
    ) -> object:
        """Execute the native CTS operation.

        Parameters
        ----------
        start : xs:string?
            A starting word.
        options : xs:string*
            Options.
        query : cts:query?
            Only include words in fragments selected by the cts:query .
        quality_weight : xs:double?
            A document quality weight to use when computing scores.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained.
        range : int | list | tuple | None
            Inclusive server-side selection; N means [1, N].
        index : int | XqyExpression | None
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        ValueHit | list
            Empty list, one parsed value, or a list of parsed values.

        Raises
        ------
        TypeError
            For unknown keywords or invalid argument types.
        ValueError
            For invalid arguments or malformed paired results.
        MarkLogicError
            For server failures, including unavailable indexes or functions.
        HTTPStatusError
            For HTTP failures without a recognized MarkLogic error.

        Notes
        -----
        Use Cts.words(...) to compose a nested expression.
        """
        expr = Cts.words(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def __init__(self, rest: AsyncRestApi, *, namespaces=None):
        """Create async search utilities using the client's REST API.

        Parameters
        ----------
        rest : AsyncRestApi
            REST API used by the expression evaluator; no request is made here.
        namespaces : dict[str, str] | None
            Default XQuery namespace declarations, copied at construction. The
            empty prefix sets the default element namespace. All execution
            methods accept namespaces overrides through keyword arguments.
        """
        self._namespaces = namespace_bindings(namespaces)
        self._eval = AsyncEvalService(rest)
        self._rest = rest

    async def _execute(
        self,
        expr,
        model,
        *,
        namespaces=None,
        database=None,
        txid=None,
        timeout=UNSET,
    ):
        """Await a service transport expression and decode paired results.

        Parameters
        ----------
        expr : XqyExpression
            Service expression producing payload/integer pairs.
        model : type
            SearchHit or ValueHit.
        namespaces : dict | None
            Effective namespace declarations for path validation and execution.
        database : str | None
            Target database.
        txid : str | None
            Existing transaction identifier.
        timeout : object
            HTTP timeout override; UNSET inherits the client configuration.

        Returns
        -------
        SearchHit | ValueHit | list
            Results preserving empty/singleton/list cardinality.

        Raises
        ------
        ValueError
            If the returned result pairs are malformed.
        MarkLogicError
            If MarkLogic rejects the evaluation.
        HTTPStatusError
            If another HTTP failure occurs.
        """
        code, variables = expr.compile(namespaces=namespaces)
        response = await self._rest.eval.post(
            xquery=code,
            variables=variables,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        return _result_pairs(response, model)

    async def search(
        self,
        expression: str | XqyExpression | None = None,
        query: XqyExpression | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,
        index: int | XqyExpression | None = None,
        xpath: str | None = None,
        **kwargs,
    ) -> object:
        """Run ``cts:search`` and return parsed SearchHit objects.

        Parameters
        ----------
        expression : str | XqyExpression | None
            Searchable path string or composed expression; None uses /.
            Literal paths are validated before execution.
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | list | tuple | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns item or [].
        xpath : str | None
            Restricted extraction XPath applied to each hit after index/range.
            Relative paths start at the hit; absolute paths start at its root.
            Uses the same namespaces as expression and preserves hit order.
            None returns hits unchanged; one hit may yield zero or many nodes.
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.search(
                expression,
                query,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
            index,
        )
        return await self._execute(
            _ResultPairs(expr, SearchHit, xpath),
            SearchHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def uris(
        self,
        *,
        start=None,
        options=None,
        query: XqyExpression | None = None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,
        index: int | XqyExpression | None = None,
        **kwargs,
    ) -> object:
        """Run ``cts:uris`` and return parsed ValueHit objects.

        Parameters
        ----------
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | list | tuple | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns item or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.uris(
                query=query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
            index,
        )
        return await self._execute(
            _ResultPairs(expr, ValueHit),
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def values(
        self,
        range_indexes,
        *,
        start=None,
        options=None,
        query: XqyExpression | None = None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,
        index: int | XqyExpression | None = None,
        **kwargs,
    ) -> object:
        """Run ``cts:values`` and return parsed ValueHit objects.

        Parameters
        ----------
        range_indexes : XqyExpression | list | tuple
            One or more native range-index reference expressions.
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | list | tuple | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns item or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.values(
                range_indexes,
                query=query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
            index,
        )
        return await self._execute(
            _ResultPairs(expr, ValueHit),
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def estimate(
        self,
        query: XqyExpression | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        maximum=None,
        **kwargs,
    ) -> int | str | bytes:
        """Run ``cts:estimate`` and return the fragment count.

        Parameters
        ----------
        query : XqyExpression | str | None
            Native query expression; None supplies an empty query slot.
        options : str | XqyExpression | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | XqyExpression | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | XqyExpression | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        maximum : int | float | XqyExpression | None
            Native maximum count; None leaves the count uncapped.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        int
            The single native aggregate result (or raw str/bytes with output_type).

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        return _single(
            await self._eval.expression(
                Cts.estimate(
                    query,
                    options=options,
                    quality_weight=quality_weight,
                    forest_ids=forest_ids,
                    maximum=maximum,
                ),
                **_execution_options(self._namespaces, kwargs),
            ),
        )
