"""Higher-level cts service (CtsService / AsyncCtsService).

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mlclient._experimental import experimental
from mlclient._options import UNSET
from mlclient.functions.xqy import (
    Cts,
    XqyCompilationContext,
    XqyExpression,
    namespace_bindings,
    xpath as xpath_expression,
)
from mlclient.models.results import SearchHit, ValueHit
from mlclient.responses import MLResponseParser

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi

Range = (
    int | list[int | XqyExpression] | tuple[int | XqyExpression, int | XqyExpression]
)
_RANGE_BOUND_COUNT = 2


def _check_lexicon_options(options) -> bool:
    """Reject literal map output and report whether options require runtime checking.

    Parameters
    ----------
    options : object
        Native lexicon options, possibly containing nested XQuery expressions.

    Returns
    -------
    bool
        Whether an expression can supply options unknown before execution.

    Raises
    ------
    ValueError
        If a literal map option requests results incompatible with ValueHit.
    """
    if isinstance(options, (list, tuple)):
        dynamic = [_check_lexicon_options(option) for option in options]
        return any(dynamic)
    if isinstance(options, str) and options == "map":
        message = "Map output is not a value sequence; use ml.eval.expression(cts...)"
        raise ValueError(message)
    return isinstance(options, XqyExpression)


class _ResultPairs(XqyExpression):
    """Pair each selected result with its native score or frequency."""

    def __init__(
        self,
        inner: XqyExpression,
        model: type,
        xpath: str | None = None,
        *,
        options=None,
    ):
        """Retain the selected expression and validate its XPath and lexicon options.

        Parameters
        ----------
        inner : XqyExpression
            Native expression after index/range selection.
        model : type
            SearchHit or ValueHit determines score versus frequency extraction.
        xpath : str | None
            Optional validated XPath applied to original search hits.
        options : object
            Lexicon options; literal map output is rejected before compilation.

        Raises
        ------
        ValueError
            If XPath is blank or a literal map option is supplied.
        TypeError
            If XPath is not a string.
        """
        self.inner = inner
        self.measure = "score" if model is SearchHit else "frequency"
        self.path = None if xpath is None else xpath_expression(xpath)
        self.check_map = model is ValueHit and _check_lexicon_options(options)

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render pairs with the measure captured before applying result XPath.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Shared external bindings and extraction-path validation.

        Returns
        -------
        str
            One XQuery sequence containing a payload and integer per result.
        """
        source = f"for $res in {self.inner.render(ctx)}\n"
        pairs = f"let $measure := cts:{self.measure}($res)\n"
        if self.path is None:
            pairs += "return ($res, $measure)"
        else:
            pairs += (
                f"for $node in $res ! {self.path.render(ctx)}\nreturn ($node, $measure)"
            )
        if self.check_map:
            return (
                source + "return if ($res instance of map:map) then\n"
                '    fn:error(fn:QName("", "MLCLIENT-LEXICON-MAP"),\n'
                '        "Map output is not a value sequence; '
                'use ml.eval.expression(cts...)")\n'
                "else\n    " + pairs.replace("\n", "\n    ")
            )
        return source + pairs


def _result_pairs(response, model: type):
    """Parse payload/measure pairs into a list of result objects.

    Parameters
    ----------
    response : httpx.Response
        Eval response produced by the service's paired expression.
    model : type
        SearchHit or ValueHit to construct from each pair.

    Returns
    -------
    list[SearchHit] | list[ValueHit]
        One object per result; an empty sequence returns an empty list.

    Raises
    ------
    ValueError
        If a payload lacks a score/frequency partner or parsing fails.
    MarkLogicError
        If the response reports a recognized server failure.
    HTTPStatusError
        If the response reports another HTTP failure.
    """
    MLResponseParser.raise_for_status(response)
    if not response.content:
        return []
    parts = MLResponseParser.parse_with_headers(response)
    if isinstance(parts, tuple) or len(parts) % 2:
        message = "CTS response is missing a score/frequency partner"
        raise ValueError(message)
    results = []
    for (headers, content), (_, measure) in zip(parts[::2], parts[1::2]):
        if model is SearchHit:
            result = SearchHit(
                content,
                score=measure,
                source_uri=headers.get("X-URI"),
                source_path=headers.get("X-Path", "/"),
            )
        else:
            result = ValueHit(
                content,
                frequency=measure,
            )
        results.append(result)
    return results


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
        self._rest = rest

    def _execute_native(
        self,
        expr,
        *,
        namespaces=None,
        database=None,
        txid=None,
        output_type=None,
        timeout=UNSET,
    ) -> list:
        """Execute a native expression and retain its result sequence.

        Parameters
        ----------
        expr : XqyExpression
            CTS operation to execute without score/frequency pairing.
        namespaces : dict | None
            Namespace declarations for compilation.
        database : str | None
            Target content database.
        txid : str | None
            Existing transaction identifier.
        output_type : type | None
            Per-item str/bytes conversion, or None for parsed values.
        timeout : object
            HTTP timeout override; UNSET inherits client configuration.

        Returns
        -------
        list
            One entry per response part; JSON arrays remain nested lists.

        Raises
        ------
        ValueError
            If output_type is not None, str or bytes.
        MarkLogicError
            If the server rejects the evaluation.
        HTTPStatusError
            If another HTTP failure occurs.
        """
        if output_type not in (None, str, bytes):
            message = "output_type must be None, str or bytes"
            raise ValueError(message)
        code, variables = expr.compile(namespaces=namespaces)
        response = self._rest.eval.post(
            xquery=code,
            variables=variables,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        MLResponseParser.raise_for_status(response)
        if not response.content:
            return []
        parts = MLResponseParser.parse_with_headers(response, output_type)
        if isinstance(parts, tuple):
            parts = [parts]
        return [content for _, content in parts]

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
        list[SearchHit] | list[ValueHit]
            A list of result objects, including for a single result.

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
    ) -> list:
        """Execute ``cts:search`` via ``/v1/eval``.

        Returns a relevance-ordered sequence of nodes specified by a given
        query.

        Parameters
        ----------
        expression : str | XqyExpression | None
            An expression to be searched. This must be an inline fully searchable path
            expression. Python strings are wrapped internally and validated
            with the other literal paths in the expression before execution.
        query : XqyExpression | None
            A cts:query specifying the search to perform. If a string is entered, the
            string is treated as a cts:word-query of the specified string.
        options : object
            Options to this search. The default is (). Options include: "filtered" A
            filtered search (the default). Filtered searches eliminate any
            false-positive matches and properly resolve cases where there are multiple
            candidate matches within the same fragment. Filtered search results fully
            satisfy the specified cts:query . "unfiltered" An unfiltered search. An
            unfiltered search selects fragments from the indexes that are candidates to
            satisfy the specified cts:query , and then it returns a single node from
            within each fragment that satisfies the specified searchable path
            expression. Unfiltered searches are useful because of the performance they
            afford when jumping deep into the result set (for example, when paginating a
            long result set and jumping to the 1,000,000th result). However, depending
            on the searchable path expression, the cts:query specified, the structure of
            the documents in the database, and the configuration of the database,
            unfiltered searches may yield false-positive results being included in the
            search results. Unfiltered searches may also result in missed matches or in
            incorrect matches, especially when there are multiple candidate matches
            within a single fragment. To avoid these problems, you should only use
            unfiltered searches on top-level XPath expressions (for example, document
            nodes, collections, directories) or on fragment roots. Using unfiltered
            searches on complex XPath expressions or on XPath expressions that traverse
            below a fragment root can result in unexpected results. "score-logtfidf"
            Compute scores using the logtfidf method (the default scoring method). This
            uses the formula: log(term frequency) * (inverse document frequency)
            "score-logtf" Compute scores using the logtf method. This does not take into
            account how many documents have the term and uses the formula: log(term
            frequency) "score-simple" Compute scores using the simple method. The
            score-simple method gives a score of 8*weight for each matching term in the
            cts:query expression, and then scales the score up by multiplying by 256. It
            does not matter how many times a given term matches (that is, the term
            frequency does not matter); each match contributes 8*weight to the score.
            For example, the following query (assume the default weight of 1) would give
            a score of 8*256=2048 for any fragment with one or more matches for "hello",
            a score of 16*256=4096 for any fragment that also has one or more matches
            for "goodbye", or a score of zero for fragments that have no matches for
            either term: cts:or-query(("hello", "goodbye")) "score-random" Compute
            scores using the random method. The score-random method gives a random value
            to the score. You can use this to randomly choose fragments matching a
            query. "score-zero" Compute all scores as zero. When combined with a quality
            weight of zero, this is the fastest consistent scoring method. "score-bm25"
            Compute scores using the bm25 method. This uses the formula: (log(term
            frequency) / (1-'bm25-length-weight'+'bm25-length-weight'*(doc length /
            average doc length))) * (inverse document frequency) "checked" Word
            positions are checked (the default) when resolving the query. Checked
            searches eliminate false-positive matches for phrases during the index
            resolution phase of search processing. "unchecked" Word positions are not
            checked when resolving the query. Unchecked searches do not take into
            account word positions and can lead to false-positive matches during the
            index resolution phase of search processing. This setting is useful for
            debugging, but not recommended for normal use. "too-many-positions-error" If
            too much memory is needed to perform positions calculations to check whether
            a document matches a query, return an XDMP-TOOMANYPOSITIONS error, instead
            of accepting the document as a match. "faceted" Do a little more work to
            save faceting information about fragments matching this search so that
            calculating facets will be faster. "unfaceted" Do not save faceting
            information about fragments matching this search. "relevance-trace" Collect
            relevance score computation details with which you can generate a trace
            report using cts:relevance-info . Collecting this information is costly and
            will significantly slow down your search, so you should only use it when
            using cts:relevance-info to tune a query. "format- FORMAT " Limit the search
            to documents in document format specified by FORMAT (binary, json, text, or
            xml) cts:order Specification A sequence of cts:order specifications. The
            order is evaluated in the order each appears in the sequence. Default:
            (cts:score-order("descending"),cts:document-order("ascending")) . The
            sequence typically consists of one or more of: cts:index-order ,
            cts:score-order , cts:confidence-order , cts:fitness-order ,
            cts:quality-order , cts:document-order , cts:unordered . When using
            cts:index-order , there must be a range index defined on the index(es)
            specified by the cts:reference specification (for example,
            cts:element-reference .) "bm25-length-weight= NUMBER " The weight of the
            document length to average document length ratio while using the
            "score-BM25" option. Valid values are greater than 0.0 and less than or
            equal to 1.0. The default is 0.333.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            (). In the XQuery version, you can use cts:search with this parameter and an
            empty cts:and-query to specify a forest-specific XPath statement (see the
            third example below). If you use this to constrain an XPath to one or more
            forests, you should set the quality-weight to zero to keep the XPath
            document order.
        range : Range | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns [item] or [].
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
        list
            Always a list; empty sequences return [] and singletons return [item].

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:search
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
    ) -> list:
        """Execute ``cts:uris`` via ``/v1/eval``.

        Returns values from the URI lexicon.

        Parameters
        ----------
        start : object
            A starting value. Return only this value and following values. If the empty
            string, return all values. If the parameter is not in the lexicon, then it
            returns the values beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" URIs should be
            returned in ascending order. "descending" URIs should be returned in
            descending order. "any" URIs from any fragment should be included.
            "document" URIs from document fragments should be included. "properties"
            URIs from properties fragments should be included. "locks" URIs from locks
            fragments should be included. "frequency-order" URIs should be returned
            ordered by frequency. "item-order" URIs should be returned ordered by item.
            "limit= N " Return no more than N URIs. You should not use this option with
            the "skip" option. Use "truncate" instead. "skip= N " Skip over fragments
            selected by the cts:query to treat the Nth fragment as the first fragment.
            URIs from skipped fragments are not included. This option affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "sample= N " Return only URIs
            from the first N fragments after skip selected by the cts:query . This
            option does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only URIs from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : XqyExpression | None
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : Range | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns [item] or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        list[str]
            Always a list; empty sequences return [] and singletons return [item].

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:uris
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
        return self._execute_native(
            expr,
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
    ) -> list:
        """Execute ``cts:values`` via ``/v1/eval``.

        Returns values from the specified value lexicon(s).

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "limit= N " Return no more than N values. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Values from skipped fragments are not
            included. This option affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "sample= N " Return only values from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only values
            from the first N fragments after skip selected by the cts:query . This
            option also affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence .
        query : XqyExpression | None
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : Range | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns [item] or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        list
            Always a list; empty sequences return [] and singletons return [item].

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:values
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
            _ResultPairs(expr, ValueHit, options=options),
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
    ) -> list:
        """Execute ``cts:estimate`` via ``/v1/eval``.

        Returns the number of fragments selected by a search.

        Parameters
        ----------
        query : XqyExpression | None
            Query to estimate. None supplies the required empty query slot.
        options : object
            Options to this search. The default is (). See cts.search for details on
            available options.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            (). In the XQuery version, you can use cts:search with this parameter and an
            empty cts:and-query to specify a forest-specific XPath statement (see the
            third example below). If you use this to constrain an XPath to one or more
            forests, you should set the quality-weight to zero to keep the XPath
            document order.
        maximum : object
            The maximum value to return. Stop selecting fragments if this number is
            reached.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        list
            One aggregate result, optionally converted with output_type.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:estimate
        """
        return self._execute_native(
            Cts.estimate(
                query,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
                maximum=maximum,
            ),
            **_execution_options(self._namespaces, kwargs),
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
    ) -> list:
        """Execute ``cts:aggregate`` via ``/v1/eval``.

        Executes a user-defined extension aggregate function against a value
        lexicon or n-way co-occurrence of multiple value lexicons.

        Parameters
        ----------
        native_plugin : object
            The path to the native plugin library containing the implementation of the
            user-defined extension aggregate.
        aggregate_name : object
            The name of an aggregate function in $native-plugin .
        range_indexes : object
            A sequence of references to range indexes. The first range index specified
            in this or any other aggregate function cannot be of type "nullable".
        argument : object
            A sequence containing the arguments for the aggregate function. A map can be
            used to pass in multiple sequences of arguments.
        options : object
            options. The default is (). Options include: "any" Co-occurrences from any
            fragment should be included. "document" Co-occurrences from document
            fragments should be included. "properties" Co-occurrences from properties
            fragments should be included. "locks" Co-occurrences from locks fragments
            should be included. "fragment-frequency" Frequency should be the number of
            fragments with an included co-occurrences. This option is used with
            cts:frequency . "item-frequency" Frequency should be the number of
            occurrences of an included co-occurrence. This option is used with
            cts:frequency . "ordered" Include co-occurrences only when the value from
            the first lexicon appears before the value from the second lexicon. Requires
            that word positions be enabled for both lexicons. "proximity= N " Include
            co-occurrences only when the values appear within N words of each other.
            Requires that word positions be enabled for both lexicons. "checked" Word
            positions should be checked when resolving the query. "unchecked" Word
            positions should not be checked when resolving the query.
            "too-many-positions-error" If too much memory is needed to perform positions
            calculations to check whether a document matches a query, return an
            XDMP-TOOMANYPOSITIONS error, instead of accepting the document as a match.
            "concurrent" Perform the work concurrently in another thread. This is a hint
            to the query optimizer to help parallelize the lexicon work, allowing the
            calling query to continue performing other work while the lexicon processing
            occurs. This is especially useful in cases where multiple lexicon calls
            occur in the same query (for example, resolving many facets in a single
            query).
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:aggregate
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
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:avg-aggregate`` via ``/v1/eval``.

        Returns the average of the values given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:avg-aggregate
        """
        expr = Cts.avg_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:classify`` via ``/v1/eval``.

        Classifies a sequence of nodes based on training data.

        Parameters
        ----------
        data_nodes : object
            The sequence of nodes to be classified.
        classifier : object
            An element node containing the classifier specification. This is typically
            the output of cts:train , either run directly or saved in an XML document in
            the database.
        options : object
            An options element . The options for classification are passed automatically
            from cts:train to the cts:classifier specification as part of the classifier
            element so that they are consistent with the parameters used in training.
            The following option may be separately passed to cts:classify and is in the
            cts:classify namespace . These options override the options present in the
            classifier item-by-item. <thresholds> A definition of the thresholds to use
            in classification. This is a complex element with one or more <threshold>
            children. You can specify both a global value and per-class values (as
            computed from cts:thresholds ). The global value will apply to any classes
            for which a per-class value is not specified. For example: <options
            xmlns="cts:classify"> <thresholds> <threshold>-1.0</threshold> <threshold
            class="Example 1">-2.42</threshold> </thresholds> </options>
        training_nodes : object
            The sequence of training nodes used to train the classifier. Required if the
            supports form of the classifier is used; ignored if the weights form of the
            classifier is used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:classify
        """
        expr = Cts.classify(
            data_nodes=data_nodes,
            classifier=classifier,
            options=options,
            training_nodes=training_nodes,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def cluster(self, nodes, *, options=None, **kwargs) -> list:
        """Execute ``cts:cluster`` via ``/v1/eval``.

        Produces a set of clusters from a sequence of nodes.

        Parameters
        ----------
        nodes : object
            The sequence of nodes to cluster.
        options : object
            An XML representation of the options for defining the clustering parameters.
            The options node must be in the cts:cluster namespace. The following is a
            sample options node: <options xmlns="cts:cluster">
            <label-max-terms>4</label-max-terms> <max-clusters>6</max-clusters>
            <use-db-config>true</use-db-config> </options> The cts:cluster options
            include: < hierarchical-levels > An integer specifying how many hierarchical
            cluster levels the clusterer should return. The default is 1 , which means
            no hierarchical clusters are returned. < label-max-terms > An integer
            specifying the maximum number of terms to use in constructing a cluster
            label. The default is 3 . < label-ignore-words > A space-separated list of
            words that are to be excluded from cluster label. The default is to not
            exclude any words. < label-ignore-attributes > A boolean that indicates
            whether attribute terms should be excluded from the cluster label. The
            default is to include terms from attributes. < details > A boolean that
            indicates whether additional details on the terms used in label generation
            are to be included in the output. See the documentation on
            cts:distinctive-terms for details on the format of the terms returned. The
            default false , meaning no such details are given. < min-clusters > An
            integer specifying a minimum number of desired clusters returned (at any
            hierarchical level). However, if no satisfactory clustering can be produced
            at a given level, only one cluster will be returned, regardless of this
            setting. The default is 3 . < max-clusters > An integer specifying a maximum
            number of clusters that can be returned (at any hierarchical level). The
            default is 15 . < overlapping > A boolean indicating whether it is
            acceptable for nodes to be assigned to more than one cluster. The default is
            false . < max-terms > An integer value specifying the maximum number of
            distinct terms to use in calculating the cluster. The default is 200 .
            Increasing the value will increase the cost (in terms of both time and
            memory) of calculating the clusters, but may improve the quality of the
            clusters. < algorithm > A value indicating which clustering algorithm to
            use, either k-means or lsi . The default is k-means . The LSI algorithm is
            significantly more expensive to compute, both in terms of time and space. <
            num-tries > Specifies the number of times to run the clusterer against the
            specified data. The default is 1. Because of the way the algorithms work,
            running the cluster multiple times will increase the number of terms, and
            tends to improve the accuratacy of the clusters. It does so at the cost of
            performance, as each time it runs, it has to do more work. < use-db-config >
            A boolean value indicating whether to use the current DB configuration for
            determining which terms to use. The default is false , which means that the
            default set of options, as well as any indexing options you specify in the
            options node, will be used for calculating the clusters and their labels.
            When set to true , any indexing options set in the context database
            configuration (including any field settings) are used, as well as any
            default settings that you have not explicitly turned off in the options
            node. The options element also includes indexing options in the
            http://marklogic.com/xdmp/database namespace. These control which terms to
            use. Note that the use of certain options, such as
            fast-case-sensitive-searches , will not impact final results unless the term
            vector size is limited with the max-terms option. Other options, such as
            phrase-throughs , will only generate terms if some other option is also
            enabled (in this case fast-phrase-searches ). The database options are the
            same as the database options shown for cts:distinctive-terms .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:cluster
        """
        expr = Cts.cluster(nodes=nodes, options=options)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:collection-match`` via ``/v1/eval``.

        Returns values from the collection lexicon that match the specified
        wildcard pattern.

        Parameters
        ----------
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" URIs should be returned in
            ascending order. "descending" URIs should be returned in descending order.
            "any" URIs from any fragment should be included. "document" URIs from
            document fragments should be included. "properties" URIs from properties
            fragments should be included. "locks" URIs from locks fragments should be
            included. "frequency-order" URIs should be returned ordered by frequency.
            "item-order" URIs should be returned ordered by item. "limit= N " Return no
            more than N collections. You should not use this option with the "skip"
            option. Use "truncate" instead. "skip= N " Skip over fragments selected by
            the cts:query to treat the Nth fragment as the first fragment. URIs from
            skipped fragments are not included. This option affects the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "sample= N " Return only URIs from the
            first N fragments after skip selected by the cts:query . This option does
            not affect the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only URIs from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:collection-match
        """
        expr = Cts.collection_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:collections`` via ``/v1/eval``.

        Returns values from the collection lexicon.

        Parameters
        ----------
        start : object
            A starting value. Return only this value and following values. If the
            parameter is not in the lexicon, then it returns the values beginning with
            the next value.
        options : object
            Options. The default is (). Options include: "ascending" URIs should be
            returned in ascending order. "descending" URIs should be returned in
            descending order. "any" URIs from any fragment should be included.
            "document" URIs from document fragments should be included. "properties"
            URIs from properties fragments should be included. "locks" URIs from locks
            fragments should be included. "frequency-order" URIs should be returned
            ordered by frequency. "item-order" URIs should be returned ordered by item.
            "limit= N " Return no more than N URIs. You should not use this option with
            the "skip" option. Use "truncate" instead. "skip= N " Skip over fragments
            selected by the cts:query to treat the Nth fragment as the first fragment.
            URIs from skipped fragments are not included. This option affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "sample= N " Return only URIs
            from the first N fragments after skip selected by the cts:query . This
            option does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only URIs from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:collections
        """
        expr = Cts.collections(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def confidence(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:confidence`` via ``/v1/eval``.

        Returns the confidence of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:confidence
        """
        expr = Cts.confidence(node=node)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def contains(self, nodes, query, **kwargs) -> list:
        """Execute ``cts:contains`` via ``/v1/eval``.

        Returns true if any of a sequence of values matches a query.

        Parameters
        ----------
        nodes : object
            The nodes or atomic values to be checked for a match. Atomic values are
            converted to a text node before checking for a match, which may result in an
            error if the value cannot be converted.
        query : object
            A query to match against. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:contains
        """
        expr = Cts.contains(nodes=nodes, query=query)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:correlation`` via ``/v1/eval``.

        Returns the frequency-weighted correlation given a 2-way co-occurrence.

        Parameters
        ----------
        value1 : object
            Reference to a range index. The type of the range index must be numeric.
        value2 : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:correlation
        """
        expr = Cts.correlation(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:count-aggregate`` via ``/v1/eval``.

        Returns the count of a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:count-aggregate
        """
        expr = Cts.count_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:covariance`` via ``/v1/eval``.

        Returns the frequency-weighted sample covariance given a 2-way co-
        occurrence.

        Parameters
        ----------
        value1 : object
            Reference to a range index. The type of the range index must be numeric.
        value2 : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:covariance
        """
        expr = Cts.covariance(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:covariance-p`` via ``/v1/eval``.

        Returns the frequency-weighted covariance of the population given a
        2-way co-occurrence.

        Parameters
        ----------
        value1 : object
            Reference to a range index. The type of the range index must be numeric.
        value2 : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:covariance-p
        """
        expr = Cts.covariance_p(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def deregister(self, id, **kwargs) -> list:
        """Execute ``cts:deregister`` via ``/v1/eval``.

        Deregister a registered query, explicitly releasing the associated
        resources.

        Parameters
        ----------
        id : object
            A registered query identifier.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:deregister
        """
        expr = Cts.deregister(id=id)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def distinctive_terms(self, nodes, *, options=None, **kwargs) -> list:
        """Execute ``cts:distinctive-terms`` via ``/v1/eval``.

        Return the most "relevant" terms in the model nodes (that is, the terms
        with the highest scores).

        Parameters
        ----------
        nodes : object
            Some model nodes.
        options : object
            An XML representation of the options for defining which terms to generate
            and how to evaluate them. The options node must be in the
            cts:distinctive-terms namespace. The following is a sample options node:
            <options xmlns="cts:distinctive-terms"> <max-terms>20</max-terms> </options>
            The cts:distinctive-terms options (which are also valid for
            cts:similar-query , cts:train , and cts:cluster ) include: < max-terms > An
            integer defining the maximum number of distinctive terms to list in the
            cts:distinctive-terms output. The default is 16. < min-val > A double
            specifying the minimum value a term can have and still be considered a
            distinctive term. The default is 0. < min-weight > A number specifying the
            minimum weighted term frequency a term can have and still be considered a
            distinctive term. In general this value will be either 0 (include unweighted
            terms) or 1 (don't include unweighted terms). The default is 1. < score > A
            string defining which scoring method to use in comparing the values of the
            terms. The default is logtfidf . See the description of scoring methods in
            the cts:search function for more details. Possible values are: logtfidf
            Compute scores using the logtfidf method. logtf Compute scores using the
            logtf method. simple Compute scores using the simple method. < complete > A
            boolean value indicating whether to return terms even if there is no query
            associated with them. The default is false . < use-db-config > The options
            below may be used to easily target a small set of terms. < use-db-config >
            is a boolean value indicating whether to use the currently configured DB
            options as defaults (overriding the built-in ones below) to determine the
            terms to generate. This is true by default. When this is false , any options
            below not explicitly specified take their default values as listed; they do
            not take the database settings' values. Flags explicitly specified override
            defaults, whether built-in (listed below), or from the database
            configuration. Flags not specified in a field apply to all fields, unless
            the field has its own setting, which will be the final value. In other words
            it's a hierarchy, with each more-specific level overriding previous
            less-specific levels. The options element also includes indexing options in
            the http://marklogic.com/xdmp/database namespace. These control which terms
            to use. These database options include the following (shown here with a db
            prefix to denote the http://marklogic.com/xdmp/database namespace . The
            default given below is the default value if use-db-config is set to false :
            < db:word-searches > Include terms for the words in the node. The default is
            false . < db:stemmed-searches > Define whether to include terms for the
            stems in the node, and at what level of stemming: off , basic , advanced ,
            or decompounding . The default is basic . < db:word-positions > Include
            terms for word positions in the node. The default is false . <
            db:fast-case-sensitive-searches > Include terms for case-sensitive
            variations of the words in the node. The default is false . <
            db:fast-diacritic-sensitive-searches > Include terms for diacritic-sensitive
            variations of the words in the node. The default is false . <
            db:fast-phrase-searches > Include terms for two-word phrases in the node.
            The default is true . < db:phrase-throughs > If phrase terms are included,
            include terms for phrases that cross the given elements. The default is to
            have no such elements. Any number can be passed in a single string,
            separated by spaces. < db:phrase-arounds > If phrase terms are included,
            include terms for phrases that skip over the given elements. The default is
            to have no such elements. Any number can be passed in a single string,
            separated by spaces. < db:fast-element-word-searches > Include terms for
            words in particular elements. The default is true . <
            db:fast-element-phrase-searches > Include terms for phrases in particular
            elements. The default is true . < db:element-word-positions > Include terms
            for element word positions in the node. The default is false . <
            db:element-word-query-throughs > Include terms for words in sub-elements of
            the given elements. The default is to have no such elements. Any number can
            be passed in a single string, separated by spaces. <
            db:fast-element-character-searches > Include terms for characters in
            particular elements. The default is false . < db:range-element-indexes >
            Include terms for data values in specific elements. The default is to have
            no such indexes. < db:range-field-indexes > Include terms for data values in
            specific fields. The default is to have no such indexes. <
            db:range-element-attribute-indexes > Include terms for data values in
            specific attributes. The default is to have no such indexes. <
            db:one-character-searches > Include terms for single character. The default
            is false . < db:two-character-searches > Include terms for two-character
            sequences. The default is false . < db:three-character-searches > Include
            terms three-character sequences. The default is false . <
            db:trailing-wildcard-searches > Include terms for trailing wildcards. The
            default is false . < db:fast-element-trailing-wildcard-searches > If
            trailing wildcard terms are included, include terms for trailing wildcards
            by element. The default is false . < db:fields > Include terms for the
            defined fields. The default is to have no fields.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:distinctive-terms
        """
        expr = Cts.distinctive_terms(nodes=nodes, options=options)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-attribute-pair-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : object
            One or more element QNames.
        latitude_names : object
            One or more element QNames.
        longitude_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Build an ``element-attribute-pair-geospatial-value-match`` call.

        Returns values from the specified element attribute pair geospatial
        value lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-pair-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element-attribute-pair geospatial
        value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences from the specified element or element-
        attribute value lexicon(s).

        Parameters
        ----------
        element_name_1 : object
            An element QName.
        attribute_name_1 : object
            An attribute QName or empty sequence. The empty sequence specifies an
            element lexicon.
        element_name_2 : object
            An element QName.
        attribute_name_2 : object
            An attribute QName or empty sequence. The empty sequence specifies an
            element lexicon.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For both lexicons, use the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "type-1= type " For the first lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the second lexicon, use the type
            specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " For
            both lexicons, use the collation specified by URI . "collation-1= URI " For
            the first lexicon, use the collation specified by URI . "collation-2= URI "
            For the second lexicon, use the collation specified by URI . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only
            co-occurrences from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence . "coordinate-system= name " Use the
            lexicon that is configured with the specified coordinate system. Allowed
            values: "wgs84", "wgs84/double", "raw", "raw/double". Only applicable if the
            lexicon value type is point or long-lat-point . "precision= value " Use the
            lexicon that is configured with the specified precision. Allowed values:
            float and double . Only applicable if the lexicon value type is point or
            long-lat-point . This value takes precedence over the precision implicit in
            the coordinate system name.
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference:
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
        return self._execute_native(
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
    ) -> list:
        """Build an ``element-attribute-value-geospatial-co-occurrences`` call.

        Returns value co-occurrences from the specified element-attribute value
        lexicon with the specified geospatial lexicon.

        Parameters
        ----------
        element_name_1 : object
            A QName identifying the parent element of the first lexicon.
        attribute_name_1 : object
            A QName identifying an attribute of element-name-1 .
        geo_element_name : object
            A QName identifying the second lexicon, which must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the coord-child-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in coord-child-name-1 and coord-child-name-2 .
        coord_child_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name identifies an element or JSON property
            geospatial lexicon.
        coord_child_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : object
            Options. The default is (). The following options are available:
            "geospatial-format= format " Use the kind of geospatial lexicon specified by
            format (element, element-child, element-pair, or element-attribute-pair). If
            neither of the child QNames is specified, the default is "element"; if only
            the first of the child QNames is specified, the default is "element-child:;
            if both child QNames are specified, the default is "element-pair". If the
            selection is not compatible with the number of geospatial QNames specified,
            an error is raised. "ascending" Co-occurrences should be returned in
            ascending order. "descending" Co-occurrences should be returned in
            descending order. "any" Co-occurrences from any fragment should be included.
            "document" Co-occurrences from document fragments should be included.
            "properties" Co-occurrences from properties fragments should be included.
            "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For the non-geospatial lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "collation= URI " For the non-geospatial lexicon, use the
            collation specified by URI . "coordinate-system= name " For the geospatial
            lexicons, use the coordinate system specified by name . Allowed values:
            "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double".
            "precision= value " Use the coordinate system at the given precision.
            Allowed values: float and double . "timezone= TZ " Return timezone sensitive
            values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay) adjusted
            to the timezone specified by TZ . Example timezones: Z, -08:00, +01:00.
            "ordered" Include co-occurrences only when the value from the first lexicon
            appears before the value from the second lexicon. Requires that word
            positions be enabled for both lexicons. "reversed" Consider the second
            lexicon as the first and vice versa. "proximity= N " Include co-occurrences
            only when the values appear within N words of each other. Requires that word
            positions be enabled for both lexicons. "limit= N " Return no more than N
            co-occurrences. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Co-occurrences from
            skipped fragments are not included. This option affects the number of
            fragments selected by the query to calculate frequencies. Only applies when
            a $query parameter is specified. "sample= N " Return only co-occurrences
            from the first N fragments after skip selected by the query . This option
            does not affect the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the query . This option affects the number of fragments selected by the
            query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference:
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
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-attribute-value-match`` via ``/v1/eval``.

        Returns values from the specified element-attribute value lexicon(s)
        that match the specified pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "item-order" Values should be returned ordered by item.
            "type= type " Use the lexicon with the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "collation= URI " Use the range index with the collation
            specified by URI . "timezone= TZ " Return timezone sensitive values
            (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay) adjusted to the
            timezone specified by TZ . Example timezones: Z, -08:00, +01:00. "limit= N "
            Return no more than N values. You should not use this option with the "skip"
            option. Use "truncate" instead. "skip= N " Skip over fragments selected by
            the cts:query to treat the Nth fragment as the first fragment. Values from
            skipped fragments are not included. This option affects the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "sample= N " Return only values from
            the first N fragments after skip selected by the cts:query . This option
            does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only values from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-value-match
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified element-attribute value
        lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "type= type " Use the lexicon with the
            type specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " Use
            the range index with the collation specified by URI . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "limit= N " Return no more than N ranges. You should not use
            this option with the "skip" option. Use "truncate" instead. "skip= N " Skip
            over fragments selected by the cts:query to treat the Nth fragment as the
            first fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentiallya while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
            "coordinate-system= name " Use the lexicon that is configured with the
            specified coordinate system. Allowed values: "wgs84", "wgs84/double", "raw",
            "raw/double". Only applicable if the lexicon value type is point or
            long-lat-point . "precision= value " Use the lexicon that is configured with
            the specified precision. Allowed values: float and double . Only applicable
            if the lexicon value type is point or long-lat-point . This value takes
            precedence over the precision implicit in the coordinate system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-value-ranges
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
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-attribute-values`` via ``/v1/eval``.

        Returns values from the specified element-attribute value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "type= type " Use
            the lexicon with the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "collation= URI " Use the range index with the collation specified by URI .
            "timezone= TZ " Return timezone sensitive values (dateTime, time, date,
            gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone specified by
            TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return no more than N
            values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the cts:query
            to treat the Nth fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "sample= N " Return only values from the
            first N fragments after skip selected by the cts:query . This option does
            not affect the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only values from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-values
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-word-match`` via ``/v1/eval``.

        Returns words from the specified element-attribute word lexicon(s) that
        match a wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-word-match
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-words`` via ``/v1/eval``.

        Returns words from the specified element-attribute word lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-words
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-child-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : object
            One or more element QNames.
        child_element_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-child-geospatial-value-match`` via ``/v1/eval``.

        Returns values from the specified element child geospatial value
        lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames identifying the parent element(s).
        child_names : object
            One or more child element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-child-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element-child geospatial value
        lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        child_names : object
            One or more child element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "score-zero" Compute all scores as zero. "checked"
            Word positions should be checked when resolving the query. "unchecked" Word
            positions should not be checked when resolving the query.
            "too-many-positions-error" If too much memory is needed to perform positions
            calculations to check whether a document matches a query, return an
            XDMP-TOOMANYPOSITIONS error, instead of accepting the document as a match.
            "eager" Perform most of the work concurrently before returning the first
            item from the indexes, and only some of the work sequentially while
            iterating through the rest of the items. This usually takes the shortest
            time for a complete item-order result or for any frequency-order result.
            "lazy" Perform only some the work concurrently before returning the first
            item from the indexes, and most of the work sequentially while iterating
            through the rest of the items. This usually takes the shortest time for a
            small item-order partial result. "concurrent" Perform the work concurrently
            in another thread. This is a hint to the query optimizer to help parallelize
            the lexicon work, allowing the calling query to continue performing other
            work while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-values
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Use the following options to customize your lexicon query: "ascending" Boxes
            should be returned in ascending order. "descending" Boxes should be returned
            in descending order. "gridded" For each side that a bucket is bounded,
            return the corresponding bound as the edge of the box, instead of the
            extremum from the points in the bucket. "empties" Include fully-bounded
            ranges whose frequency is 0. Only empty ranges that have both their upper
            and lower bounds specified in the $bounds options are returned; any empty
            ranges that are less than the first bound or greater than the last bound are
            not returned. For example, if you specify 4 bounds and there are no results
            for any of the bounds, 3 elements are returned (not 5 elements). "any"
            Points from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon that is
            configured with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-geospatial-value-match`` via ``/v1/eval``.

        Returns values from the specified element geospatial value lexicon(s)
        that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-geospatial-value-match
        """
        expr = Cts.element_geospatial_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element geospatial value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-geospatial-values
        """
        expr = Cts.element_geospatial_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-pair-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : object
            One or more element QNames.
        latitude_names : object
            One or more element QNames.
        longitude_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-pair-geospatial-value-match`` via ``/v1/eval``.

        Returns values from the specified element pair geospatial value
        lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-pair-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element-pair geospatial value
        lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames identifying the parent element of the latitude
            and longitude elements.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-values
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified element value
        lexicon(s).

        Parameters
        ----------
        element_name_1 : object
            An element QName.
        element_name_2 : object
            An element QName.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For both lexicons, use the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "type-1= type " For the first lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the second lexicon, use the type
            specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " For
            both lexicons, use the collation specified by URI . "collation-1= URI " For
            the first lexicon, use the collation specified by URI . "collation-2= URI "
            For the second lexicon, use the collation specified by URI . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only
            co-occurrences from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence . "coordinate-system= name " Use
            lexicons configured with the specified coordinate system. Allowed values:
            "wgs84", "wgs84/double", "raw", "raw/double". Only applicable if the lexicon
            value type is point or long-lat-point . "precision= value " Use lexicons
            configured with the specified precision. Allowed values: float and double .
            Only applicable if the lexicon value type is point or long-lat-point . This
            value takes precedence over the precision implicit in the coordinate system
            name.
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-value-co-occurrences
        """
        expr = Cts.element_value_co_occurrences(
            element_name_1=element_name_1,
            element_name_2=element_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-value-geospatial-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences from the specified element value lexicon
        with the specified geospatial lexicon.

        Parameters
        ----------
        element_name_1 : object
            A QName identifying the first lexicon. If this is a geospatial lexicon, it
            can only be an element geospatial lexicon. You should usually use
            cts:geospatial-co-occurrences to find co-occurrences between two geospatial
            lexicons.
        geo_element_name : object
            A QName identifying the second lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the coord-child-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in coord-child-name-1 and coord-child-name-2 .
        coord_child_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name identifies an element or JSON property
            geospatial lexicon.
        coord_child_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : object
            Options. The default is (). The following options are available:
            "geospatial-format= format " Use the kind of geospatial lexicon specified by
            format (element, element-child, element-pair, or element-attribute-pair). If
            neither of the child QNames is specified, the default is "element"; if only
            the first of the child QNames is specified, the default is "element-child:;
            if both child QNames are specified, the default is "element-pair". If the
            selection is not compatible with the number of geospatial QNames specified,
            an error is raised. "ascending" Co-occurrences should be returned in
            ascending order. "descending" Co-occurrences should be returned in
            descending order. "any" Co-occurrences from any fragment should be included.
            "document" Co-occurrences from document fragments should be included.
            "properties" Co-occurrences from properties fragments should be included.
            "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For the non-geospatial lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the geospatial lexicon, use the type
            specified by type-2 (point or long-lat-point) "collation= URI " For the
            non-geospatial lexicon, use the collation specified by URI .
            "coordinate-system= name " Use the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "ordered" Include co-occurrences only when the value from
            the first lexicon appears before the value from the second lexicon. Requires
            that word positions be enabled for both lexicons. "reversed" Consider the
            second lexicon as the first and vice versa. "proximity= N " Include
            co-occurrences only when the values appear within N words of each other.
            Requires that word positions be enabled for both lexicons. "limit= N "
            Return no more than N co-occurrences. You should not use this option with
            the "skip" option. Use "truncate" instead. "skip= N " Skip over fragments
            selected by the query to treat the Nth matching fragment as the first
            fragment. Co-occurrences from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only co-occurrences from the first N fragments after skip selected by
            the query . This option does not affect the number of fragments selected by
            the query to calculate frequencies. Only applies when a $query parameter is
            specified. "truncate= N " Include only co-occurrences from the first N
            fragments after skip selected by the query . This option affects the number
            of fragments selected by the query to calculate frequencies. Only applies
            when a $query parameter is specified. "score-logtfidf" Compute scores using
            the logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference:
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
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-value-match`` via ``/v1/eval``.

        Returns values from the specified element value lexicon(s) that match
        the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "type= type " Use the lexicon with the type specified by
            type (int, unsignedInt, long, unsignedLong, float, double, decimal,
            dateTime, time, date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration,
            dayTimeDuration, string, or anyURI) "collation= URI " Use the range index
            with the collation specified by URI . "timezone= TZ " Return timezone
            sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay)
            adjusted to the timezone specified by TZ . Example timezones: Z, -08:00,
            +01:00. "limit= N " Return no more than N values. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only values from the first N fragments after skip selected by the
            cts:query . This option does not affect the number of fragments selected by
            the cts:query to calculate frequencies. Only applies when a $query parameter
            is specified. "truncate= N " Include only values from the first N fragments
            after skip selected by the cts:query . This option also affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "score-logtfidf" Compute
            scores using the logtfidf method. Only applies when a $query parameter is
            specified. "score-logtf" Compute scores using the logtf method. Only applies
            when a $query parameter is specified. "score-simple" Compute scores using
            the simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-value-match
        """
        expr = Cts.element_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified element value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "type= type " Use the lexicon with the
            type specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " Use
            the lexicon with the collation specified by URI . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "limit= N " Return no more than N ranges. You should not use
            this option with the "skip" option. Use "truncate" instead. "skip= N " Skip
            over fragments selected by the cts:query to treat the Nth fragment as the
            first fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
            "coordinate-system= name " Use the lexicon that is configured with the
            specified coordinate system. Allowed values: "wgs84", "wgs84/double", "raw",
            "raw/double". Only applicable if the lexicon value type is point or
            long-lat-point . "precision= value " Use the lexicon that is configured with
            the specified precision. Allowed values: float and double . Only applicable
            if the lexicon value type is point or long-lat-point . This value takes
            precedence over the precision implicit in the coordinate system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-value-ranges
        """
        expr = Cts.element_value_ranges(
            element_names=element_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-values`` via ``/v1/eval``.

        Returns values from the specified element value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames. If you specify multiple lexicons, they must all
            be over the same value type (string, int, etc.).
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "type= type " Use
            the lexicon with the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "collation= URI " Use the lexicon with the collation specified by URI .
            "timezone= TZ " Return timezone sensitive values (dateTime, time, date,
            gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone specified by
            TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return no more than N
            words. You should not use this option with the "skip" option. Use "truncate"
            instead. "skip= N " Skip over fragments selected by the cts:query to treat
            the Nth fragment as the first fragment. Values from skipped fragments are
            not included. This option affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "sample= N " Return only values from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only values
            from the first N fragments after skip selected by the cts:query . This
            option also affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-values
        """
        expr = Cts.element_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def element_walk(self, node, element, expr, **kwargs) -> list:
        """Execute ``cts:element-walk`` via ``/v1/eval``.

        Returns a copy of the node, replacing any elements found with the
        specified expression.

        Parameters
        ----------
        node : object
            A node to run the walk over. The node must be either a document node or an
            element node; it cannot be a text node.
        element : object
            The name of elements to replace.
        expr : object
            An expression with which to replace each match. You can use the variables
            $cts:node and $cts:action (described below) in the expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-walk
        """
        expr = Cts.element_walk(node=node, element=element, expr=expr)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-word-match`` via ``/v1/eval``.

        Returns words from the specified element word lexicon(s) that match a
        wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-word-match
        """
        expr = Cts.element_word_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-words`` via ``/v1/eval``.

        Returns words from the specified element word lexicon.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-words
        """
        expr = Cts.element_words(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def entity_dictionary_get(self, uri, **kwargs) -> list:
        """Execute ``cts:entity-dictionary-get`` via ``/v1/eval``.

        Retrieve an entity dictionary previously cached in the database.

        Parameters
        ----------
        uri : object
            URI of a previously saved entity dictionary.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:entity-dictionary-get
        """
        expr = Cts.entity_dictionary_get(uri=uri)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def entity_highlight(self, node, expr, *, dict=None, **kwargs) -> list:
        """Execute ``cts:entity-highlight`` via ``/v1/eval``.

        Returns a copy of the node, replacing any entities found with the
        specified expression.

        Parameters
        ----------
        node : object
            A node to run entity highlight on. The node must be either a document node
            or an element node; it cannot be a text node.
        expr : object
            An expression with which to replace each match. You can use the variables
            $cts:text , $cts:node , $cts:entity-type and $cts:normalized-text ,
            $cts:start , and $cts:action (described below) in the expression.
        dict : object
            The entity dictionary to use for matching entities in the text of the input
            node. If you omit this parameter, the default entity dictionary is used. (No
            default dictionaries currently exist.) See the Usage Notes for details.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:entity-highlight
        """
        expr = Cts.entity_highlight(node=node, expr=expr, dict=dict)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def entity_walk(self, node, expr, *, dict=None, **kwargs) -> list:
        """Execute ``cts:entity-walk`` via ``/v1/eval``.

        Walk an XML document or element node, evaluating an expression against
        any matching entities.

        Parameters
        ----------
        node : object
            A node to walk. The node must be either an XML document node or an XML
            element node; it cannot be a text node.
        expr : object
            An expression to evaluate for each match. You can use the variables
            $cts:text , $cts:node , $cts:entity-type , $cts:normalized-text ,
            $cts:entity-id , $cts:start , and $cts:action in the expression. See the
            Usage Notes for details.
        dict : object
            The entity dictionary to use for matching entities in the text of the input
            node. If you omit this parameter, the default entity dictionary is used. (No
            default dictionaries currently exist.) See the Usage Notes for details.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:entity-walk
        """
        expr = Cts.entity_walk(node=node, expr=expr, dict=dict)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:field-value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified field value lexicon(s).

        Parameters
        ----------
        field_name_1 : object
            A string.
        field_name_2 : object
            A string.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For both lexicons, use the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "type-1= type " For the first lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the second lexicon, use the type
            specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " For
            both lexicons, use the collation specified by URI . "collation-1= URI " For
            the first lexicon, use the collation specified by URI . "collation-2= URI "
            For the second lexicon, use the collation specified by URI . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. Return only co-occurrences from the
            first N fragments after skip selected by the cts:query , bit do not affect
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the cts:query . This option also affects the number of fragments selected
            by the cts:query to calculate frequencies. Only applies when a $query
            parameter is specified. "score-logtfidf" Compute scores using the logtfidf
            method. Only applies when a $query parameter is specified. "score-logtf"
            Compute scores using the logtf method. Only applies when a $query parameter
            is specified. "score-simple" Compute scores using the simple method. Only
            applies when a $query parameter is specified. "score-random" Compute scores
            using the random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence . "coordinate-system= name " Use the
            lexicon that is configured with the specified coordinate system. Allowed
            values: "wgs84", "wgs84/double", "raw", "raw/double". Only applicable if the
            lexicon value type is point or long-lat-point . "precision= value " Use the
            lexicon that is configured with the specified precision. Allowed values:
            float and double . Only applicable if the lexicon value type is point or
            long-lat-point . This value takes precedence over the precision implicit in
            the coordinate system name.
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:field-value-co-occurrences
        """
        expr = Cts.field_value_co_occurrences(
            field_name_1=field_name_1,
            field_name_2=field_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:field-value-match`` via ``/v1/eval``.

        Returns values from the specified field value lexicon(s) that match the
        specified wildcard pattern.

        Parameters
        ----------
        field_names : object
            One or more field names.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "type= type " Use the lexicon with the type specified by
            type (int, unsignedInt, long, unsignedLong, float, double, decimal,
            dateTime, time, date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration,
            dayTimeDuration, string, or anyURI) "collation= URI " Use the range index
            with the collation specified by URI . "timezone= TZ " Return timezone
            sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay)
            adjusted to the timezone specified by TZ . Example timezones: Z, -08:00,
            +01:00. "limit= N " Return no more than N values. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only values from the first N fragments after skip selected by the
            cts:query . This option does not affect the number of fragments selected by
            the cts:query to calculate frequencies. Only applies when a $query parameter
            is specified. "truncate= N " Include only values from the first N fragments
            after skip selected by the cts:query . This option also affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "score-logtfidf" Compute
            scores using the logtfidf method. Only applies when a $query parameter is
            specified. "score-logtf" Compute scores using the logtf method. Only applies
            when a $query parameter is specified. "score-simple" Compute scores using
            the simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-value-match
        """
        expr = Cts.field_value_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:field-value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified field value lexicon(s).

        Parameters
        ----------
        field_names : object
            One or more element QNames.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "type= type " Use the lexicon with the
            type specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " Use
            the lexicon with the collation specified by URI . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "limit= N " Return no more than N ranges. You should not use
            this option with the "skip" option. Use "truncate" instead. "skip= N " Skip
            over fragments selected by the cts:query to treat the Nth fragment as the
            first fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
            "coordinate-system= name " Use the lexicon that is configured with the
            specified coordinate system. Allowed values: "wgs84", "wgs84/double", "raw",
            "raw/double". Only applicable if the lexicon value type is point or
            long-lat-point . "precision= value " Use the lexicon that is configured with
            the specified precision. Allowed values: float and double . Only applicable
            if the lexicon value type is point or long-lat-point . This value takes
            precedence over the precision implicit in the coordinate system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:field-value-ranges
        """
        expr = Cts.field_value_ranges(
            field_names=field_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:field-values`` via ``/v1/eval``.

        Returns values from the specified field value lexicon(s).

        Parameters
        ----------
        field_names : object
            One or more field names.
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "type= type " Use
            the lexicon with the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "collation= URI " Use the lexicon with the collation specified by URI .
            "timezone= TZ " Return timezone sensitive values (dateTime, time, date,
            gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone specified by
            TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return no more than N
            words. You should not use this option with the "skip" option. Use "truncate"
            instead. "skip= N " Skip over fragments selected by the cts:query to treat
            the Nth fragment as the first fragment. Values from skipped fragments are
            not included. This option affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "sample= N " Return only values from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only values
            from the first N fragments after skip selected by the cts:query . This
            option also affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence .
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-values
        """
        expr = Cts.field_values(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:field-word-match`` via ``/v1/eval``.

        Returns words from the specified field word lexicon(s) that match a
        wildcard pattern.

        Parameters
        ----------
        field_names : object
            One or more field names.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth matching fragment as
            the first fragment. Words from skipped fragments are not included. Only
            applies when a $query parameter is specified. "sample= N " Return only words
            from the first N fragments after skip selected by the cts:query . Only
            applies when a $query parameter is specified. "truncate= N " Include only
            words from the first N fragments after skip selected by the cts:query . Only
            applies when a $query parameter is specified. "score-logtfidf" Compute
            scores using the logtfidf method. Only applies when a $query parameter is
            specified. "score-logtf" Compute scores using the logtf method. Only applies
            when a $query parameter is specified. "score-simple" Compute scores using
            the simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-word-match
        """
        expr = Cts.field_word_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:field-words`` via ``/v1/eval``.

        Returns words from the specified field word lexicon.

        Parameters
        ----------
        field_names : object
            One or more field names.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-words
        """
        expr = Cts.field_words(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    def fitness(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:fitness`` via ``/v1/eval``.

        Returns the fitness of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:fitness
        """
        expr = Cts.fitness(node=node)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def frequency(self, value, **kwargs) -> list:
        """Execute ``cts:frequency`` via ``/v1/eval``.

        Returns an integer representing the number of times in which a
        particular value occurs in a value lexicon lookup.

        Parameters
        ----------
        value : object
            A value from a lexicon lookup function. For example, a value returned by a
            function such as cts:values , cts:words , cts:field-values ,
            cts:field-word-match , or cts:geospatial-boxes .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:frequency
        """
        expr = Cts.frequency(value=value)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified point lexicon(s).

        Parameters
        ----------
        geo_indexes : object
            A sequence of references to geospatial indexes.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:geospatial-co-occurrences`` via ``/v1/eval``.

        Find value co-occurrences from two geospatial lexicons.

        Parameters
        ----------
        geo_element_name_1 : object
            A QName identifying the first lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the child-1-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in child-1-name-1 and child-1-name-2 .
        geo_element_name_2 : object
            A QName identifying the first lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the child-2-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in child-2-name-1 and child-2-name-2 .
        child_1_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-1 that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name-1 identifies an element or JSON property
            geospatial lexicon.
        child_1_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-1 that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        child_2_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-2 that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name-2 identifies an element or JSON property
            geospatial lexicon.
        child_2_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-2 that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : object
            Options. The default is (). The following options are available:
            "geospatial-format= format " For both geospatial lexicons, use the kind of
            geospatial lexicon specified by format (element, element-child,
            element-pair, or element-attribute-pair). If neither of the child QNames is
            specified, the default is "element"; if only the first of the child QNames
            is specified, the default is "element-child:; if both child QNames are
            specified, the default is "element-pair". If the selection is not compatible
            with the number of geospatial QNames specified, an error is raised.
            "geospatial-format-1= format " For the first geospatial lexicon, use the
            kind of geospatial lexicon specified by format (element, element-child,
            element-pair, or element-attribute-pair). If neither of the child QNames is
            specified, the default is "element"; if only the first of the child QNames
            is specified, the default is "element-child:; if both child QNames are
            specified, the default is "element-pair". If the selection is not compatible
            with the number of geospatial QNames specified, an error is raised.
            "geospatial-format-2= format " For the second geospatial lexicons, use the
            kind of geospatial lexicon specified by format (element, element-child,
            element-pair, or element-attribute-pair). If neither of the child QNames is
            specified, the default is "element"; if only the first of the child QNames
            is specified, the default is "element-child:; if both child QNames are
            specified, the default is "element-pair". If the selection is not compatible
            with the number of geospatial QNames specified, an error is raised.
            "ascending" Co-occurrences should be returned in ascending order.
            "descending" Co-occurrences should be returned in descending order. "any"
            Co-occurrences from any fragment should be included. "document"
            Co-occurrences from document fragments should be included. "properties"
            Co-occurrences from properties fragments should be included. "locks"
            Co-occurrences from locks fragments should be included. "frequency-order"
            Co-occurrences should be returned ordered by frequency. "item-order"
            Co-occurrences should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included co-occurrences.
            This option is used with cts:frequency . "item-frequency" Frequency should
            be the number of occurrences of an included co-occurrence. This option is
            used with cts:frequency . "coordinate-system= name " For both geospatial
            lexicons, use the coordinate system specified by name . Allowed values:
            "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double".
            "coordinate-system-1= string " For the first geospatial lexicon, use the
            coordinate system specified by name . "coordinate-system-2= string " For the
            second geospatial lexicons, use the coordinate system specified by name .
            "ordered" Include co-occurrences only when the value from the first lexicon
            appears before the value from the second lexicon. Requires that word
            positions be enabled for both lexicons. "reversed" Consider the second
            lexicon as the first and vice versa. "proximity= N " Include co-occurrences
            only when the values appear within N words of each other. Requires that word
            positions be enabled for both lexicons. "limit= N " Return no more than N
            co-occurrences. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Co-occurrences from
            skipped fragments are not included. This option affects the number of
            fragments selected by the query to calculate frequencies. Only applies when
            a $query parameter is specified. "sample= N " Return only co-occurrences
            from the first N fragments after skip selected by the query . This option
            does not affect the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the query . This option affects the number of fragments selected by the
            query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:geospatial-co-occurrences
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
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def highlight(self, node, query, expr, **kwargs) -> list:
        """Execute ``cts:highlight`` via ``/v1/eval``.

        Returns a copy of the node, replacing any text matching the query with
        the specified expression.

        Parameters
        ----------
        node : object
            A node to highlight. The node must be either a document node or an element
            node; it cannot be a text node.
        query : object
            A query specifying the text to highlight. If a string is entered, the string
            is treated as a cts:word-query of the specified string.
        expr : object
            An expression with which to replace each match. You can use the variables
            $cts:text , $cts:node , $cts:queries , $cts:start , and $cts:action
            (described below) in the expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:highlight
        """
        expr = Cts.highlight(node=node, query=query, expr=expr)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:json-property-word-match`` via ``/v1/eval``.

        Returns words from the specified JSON property word lexicon(s) that
        match a wildcard pattern.

        Parameters
        ----------
        property_names : object
            One or more property names.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:json-property-word-match
        """
        expr = Cts.json_property_word_match(
            property_names=property_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:json-property-words`` via ``/v1/eval``.

        Returns words from the specified JSON property word lexicon.

        Parameters
        ----------
        property_names : object
            One or more property names.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:json-property-words
        """
        expr = Cts.json_property_words(
            property_names=property_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:linear-model`` via ``/v1/eval``.

        Returns a linear model that fits the frequency-weighted data set.

        Parameters
        ----------
        values : object
            References to two range indexes. The types of the range indexes must be
            numeric. If the size of this sequence is not 2, the function returns the
            empty sequence.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:linear-model
        """
        expr = Cts.linear_model(
            values=values,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:match-regions`` via ``/v1/eval``.

        Find regions in documents that have a spatial relationship to one or
        more caller-supplied regions.

        Parameters
        ----------
        range_indexes : object
            References to range indexes that store the string serialization of regions
            to match against.
        operation : object
            The operation to test. Must be one of the following: contains , covered-by ,
            covers , crosses , disjoint , equals , intersects , overlaps , touches ,
            within . See the Usage Notes for details.
        regions : object
            One or more cts:region values to test against. A region matches if it
            matches against any of these regions.
        options : object
            String options you can use to control the operation. The following options
            are supported: "coordinate-system= value " Use the given coordinate system.
            Valid values are wgs84 , wgs84/double , etrs89 , etrs89/double , raw and
            raw/double . Defaults to the governing coordinating system. "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . Defaults to the precision of the governing coordinate
            system. "units= value " Compute distances and radii of circles using the
            given units. Allowed values: miles (default), km , feet , and meters .
            "strings" Return results as strings instead of as cts:region values. "any"
            Co-occurrences from any fragment should be included. "document"
            Co-occurrences from document fragments should be included. "properties"
            Co-occurrences from properties fragments should be included. "locks"
            Co-occurrences from locks fragments should be included. "fragment-frequency"
            Frequency should be the number of fragments with an included co-occurrence.
            This option is used with cts:frequency . "item-frequency" Frequency should
            be the number of occurrences of an included co-occurrence. This option is
            used with cts:frequency . "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query).
        query : object
            Limit the region comparison to documents that match this query. Also,
            compute frequencies from the set of included regions. The values do not need
            to match the query, but they must occur in fragments selected by the query.
            The fragments are not filtered to ensure they match the query. Instead, they
            are selected in the same manner as "unfiltered" cts:search operations.
        forest_ids : object
            A sequence of IDs of forests to which the search should be constrained. An
            empty sequence means search all forests in the database. The default is an
            empty sequence.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:match-regions
        """
        expr = Cts.match_regions(
            range_indexes=range_indexes,
            operation=operation,
            regions=regions,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:max`` via ``/v1/eval``.

        Returns the maximal value given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:max
        """
        expr = Cts.max(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def median(self, arg, **kwargs) -> list:
        """Execute ``cts:median`` via ``/v1/eval``.

        Returns a frequency-weighted median of a sequence.

        Parameters
        ----------
        arg : object
            The sequence of values. The values should be the result of a lexicon lookup.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:median
        """
        expr = Cts.median(arg=arg)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:min`` via ``/v1/eval``.

        Returns the minimal value given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:min
        """
        expr = Cts.min(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def part_of_speech(self, token, **kwargs) -> list:
        """Execute ``cts:part-of-speech`` via ``/v1/eval``.

        Returns the part of speech for a cts:token, if any.

        Parameters
        ----------
        token : object
            A token, as returned from cts:tokenize .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:part-of-speech
        """
        expr = Cts.part_of_speech(token=token)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def percent_rank(self, arg, value, *, options=None, **kwargs) -> list:
        """Execute ``cts:percent-rank`` via ``/v1/eval``.

        Returns the rank of a value in a data set as a percentage of the data
        set.

        Parameters
        ----------
        arg : object
            The sequence of values.
        value : object
            The value to be "ranked".
        options : object
            Options. The default is (). Options include: "ascending"(default) Rank the
            value as if the sequence was sorted in ascending order. "descending" Rank
            the value as if the sequence was sorted in descending order. "collation= URI
            " Applies only when $arg is of the xs:string type. If no specified, the
            default collation is used. "coordinate-system= name " Applies only when $arg
            is of the cts:point type. If no specified, the default coordinate system is
            used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:percent-rank
        """
        expr = Cts.percent_rank(arg=arg, value=value, options=options)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def percentile(self, arg, p, **kwargs) -> list:
        """Execute ``cts:percentile`` via ``/v1/eval``.

        Returns a sequence of percentile(s) given a sequence of percentage(s).

        Parameters
        ----------
        arg : object
            The sequence of values. The values should be the result of a lexicon lookup.
        p : object
            The sequence of percentage(s).
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:percentile
        """
        expr = Cts.percentile(arg=arg, p=p)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def period_compare(self, period_1, operator, period_2, **kwargs) -> list:
        """Execute ``cts:period-compare`` via ``/v1/eval``.

        Compares two periods using the specified comparison operator.

        Parameters
        ----------
        period_1 : object
            The first period to compare.
        operator : object
            A comparison operator.
        period_2 : object
            The second period to compare against the first.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:period-compare
        """
        expr = Cts.period_compare(
            period_1=period_1,
            operator=operator,
            period_2=period_2,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def quality(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:quality`` via ``/v1/eval``.

        Returns the quality of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:quality
        """
        expr = Cts.quality(node=node)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def rank(self, arg, value, *, options=None, **kwargs) -> list:
        """Execute ``cts:rank`` via ``/v1/eval``.

        Returns the rank of a value in a data set.

        Parameters
        ----------
        arg : object
            The sequence of values.
        value : object
            The value to be "ranked".
        options : object
            Options. The default is (). Options include: "ascending"(default) Rank the
            value as if the sequence was sorted in ascending order. "descending" Rank
            the value as if the sequence was sorted in descending order. "collation= URI
            " Applies only when $arg is of the xs:string type. If no specified, the
            default collation is used. "coordinate-system= name " Applies only when $arg
            is of the cts:point type. If no specified, the default coordinate system is
            used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:rank
        """
        expr = Cts.rank(arg=arg, value=value, options=options)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def register(self, query, **kwargs) -> list:
        """Execute ``cts:register`` via ``/v1/eval``.

        Register a query for later use.

        Parameters
        ----------
        query : object
            A query to register.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:register
        """
        expr = Cts.register(query=query)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def relevance_info(self, *, node=None, output_kind=None, **kwargs) -> list:
        """Execute ``cts:relevance-info`` via ``/v1/eval``.

        Return the relevance score computation report for a node.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation. If this parameter is omitted, the context node is used.
        output_kind : object
            The output kind. It can be either "element" or "object". With "element", the
            built-in returns an XML element. With "object", the built-in returns a
            map:map. The default is "element".
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:relevance-info
        """
        expr = Cts.relevance_info(node=node, output_kind=output_kind)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def remainder(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:remainder`` via ``/v1/eval``.

        Returns an estimated search result size for a node, or of the context
        node if no node is provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation. If you specify the first item from a cts:search expression, then
            cts:remainder will return an estimate of the number of fragments that match
            that expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:remainder
        """
        expr = Cts.remainder(node=node)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def score(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:score`` via ``/v1/eval``.

        Returns the score of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:score
        """
        expr = Cts.score(node=node)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:stddev`` via ``/v1/eval``.

        Returns a frequency-weighted sample standard deviation given a value
        lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:stddev
        """
        expr = Cts.stddev(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:stddev-p`` via ``/v1/eval``.

        Returns a frequency-weighted standard deviation of the population given
        a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:stddev-p
        """
        expr = Cts.stddev_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def stem(self, text, *, language=None, part_of_speech=None, **kwargs) -> list:
        """Execute ``cts:stem`` via ``/v1/eval``.

        Returns the stem(s) for a word.

        Parameters
        ----------
        text : object
            A word or phrase to stem.
        language : object
            A language to use for stemming. If not supplied, it uses the database
            default language.
        part_of_speech : object
            A part of speech to use for stemming. The default is the unspecified part of
            speech. This parameter is for testing custom stemmers.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:stem
        """
        expr = Cts.stem(text=text, language=language, part_of_speech=part_of_speech)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:sum-aggregate`` via ``/v1/eval``.

        Returns the sum of the values given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:sum-aggregate
        """
        expr = Cts.sum_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:thresholds`` via ``/v1/eval``.

        Compute precision, recall, the F measure, and thresholds for the classes
        computed by the classifier, by comparing with the labels for the same
        set.

        Parameters
        ----------
        computed_labels : object
            A sequence of element nodes containing the labels from classification (the
            output from cts:classify ) for a set of documents.
        known_labels : object
            A sequence of element nodes containing the known labels for the same set of
            documents.
        recall_weight : object
            The factor to use in the calculation of the F measure. The number should be
            non-negative. A value of 0 means F is just precision and a value of +INF
            means F is just recall. The default is 1, which gives the harmonic mean
            between precision and recall.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:thresholds
        """
        expr = Cts.thresholds(
            computed_labels=computed_labels,
            known_labels=known_labels,
            recall_weight=recall_weight,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def tokenize(self, text, *, language=None, field=None, **kwargs) -> list:
        """Execute ``cts:tokenize`` via ``/v1/eval``.

        Tokenizes text into words, punctuation, and spaces.

        Parameters
        ----------
        text : object
            A word or phrase to tokenize.
        language : object
            A language to use for tokenization. If not supplied, it uses the database
            default language.
        field : object
            A field to use for tokenization. If the field has custom tokenization rules,
            they will be used. If no field is supplied or the field has no custom
            tokenization rules, the default tokenization rules are used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:tokenize
        """
        expr = Cts.tokenize(text=text, language=language, field=field)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def train(self, training_nodes, labels, *, options=None, **kwargs) -> list:
        """Execute ``cts:train`` via ``/v1/eval``.

        Produces a set of classifiers from a list of labeled training documents.

        Parameters
        ----------
        training_nodes : object
            The sequence of training nodes. These are nodes that represent members of
            the classes.
        labels : object
            A sequence of labels for the training nodes, in the order corresponding to
            the training nodes.
        options : object
            Options with which to customize this operation. You can specify options as
            either an XML element in the "cts:train" namespace, or as a map:map . The
            options names below are XML element localnames. When using a map, replace
            the hyphens with camel casing. For example, "an-option" becomes "anOption"
            when used as a map:map key. The following is a sample options node :
            <options xmlns="cts:train"> <classifier-type>supports</classifier-type>
            <kernel>geodesic</kernel> </options> This function supports the following
            options: < classifier-type > A string defining the kind of classifier to
            produce, either weights or supports . The default is weights . < kernel > A
            string defining which function to use for comparing documents. The default
            is sqrt . Normalization (the values that end in -normalized ) brings
            document vectors into the unit sphere, which may improve the mathematical
            properties of the calculations. Possible values are: simple Model documents
            as 1 or 0 for presence or absence of each term. simple-normalized Like
            simple , but normalized by the square root of the document length. sqrt
            Model documents using the square root of the term frequencies.
            sqrt-normalized Like sqrt , but normalized by the sum of the term
            frequencies. linear-normalized Model documents as the term frequencies
            normalized by the square root of the sum of the squares of the term
            frequencies. gaussian Compare documents using the Gaussian of the term
            frequencies. Requires a classifier-type of supports . geodesic Compare
            documents using the Riemann geodesic distance over term frequencies.
            Requires a classifier-type of supports . < max-terms > An integer defining
            the maximum number of terms to use to represent each document. If a positive
            number M is given, then the M most discriminating terms are used; other
            terms are dropped. The default is 0 (unlimited), but for larger documents a
            value in 500 to 1000 range will produce much better results. < max-support >
            A double specifying the maximum influence a single training node can have.
            This parameter has a strong influence on performance. The default value of
            1.0 should work well in most cases. Larger values means greater sensitivity
            and may improve accuracy on small datasets, but give longer running times.
            Smaller values mean less sensitivity and better resistance to mis-classified
            documents, and shorter running times. < min-weight > A double specifying the
            minimum weight a term can have and still be considered for inclusion in the
            term vector. This parameter only applies to the term weight form of the
            classifier. Smaller values mean longer term vectors and as a consequence
            longer running times and greater memory consumption during classification,
            but may also improve accuracy. The initial value may be adjusted downwards
            during training if a class would otherwise have no terms in its output
            vector. The default is is 0.01. < tolerance > How close the final solutions
            to the constraint equations must be. Smaller values lead to a greater number
            of iterations and longer running times. Larger values lead to less precise
            classification. The default is 0.01. < epsilon > How close a value must be
            to 0 to be counted as equal to 0. Since double arithmetic is not precise,
            setting this value to exactly 0 will likely lead to non-convergence of the
            algorithm. Smaller values lead to a greater number of iterations and longer
            running times. Larger values lead to less precise classification. The
            initial value may be adjusted downwards during execution if it is too large
            to be useful. In general the higher the dimensionality (larger documents,
            larger limits on the number of terms), the smaller this should be. The
            default is 0.01. < max-iterations > The maximum number of iterations of the
            constraint satisfaction algorithm to run. The algorithm usually converges
            very quickly, so this parameter usually has no effect unless it is set very
            low. The default is 500. <thresholds> A definition of the thresholds to use
            in classification. This is a complex element with one or more <threshold>
            children. You can specify both a default value and per-class values (as
            computed from cts:thresholds ). The default value will apply to any classes
            for which a per-class value is not specified. For example: <options
            xmlns="cts:train"> <thresholds> <threshold>-1.0</threshold> <threshold
            class="Example 1">-2.42</threshold> </thresholds> </options> For the initial
            tuning phase of training your data, leave the value of this parameter at its
            default value which is a very large negative number (-1.0e30). This will
            allow you to accurately compute the threshold values when you run
            cts:thresholds on the initial training data. Then you can use the calculated
            threshold values when you run the secondary pass through the second part of
            your training data. < use-db-config > A boolean value indicating whether to
            use the current DB configuration for determining which terms to use. The
            default is false , which means that only the indexing options in the options
            node will be used for calculating the classifier. The options element also
            includes indexing options in the http://marklogic.com/xdmp/database
            namespace. These control which terms to use. Note that the use of certain
            options, such as fast-case-sensitive-searches , will not impact final
            results unless the term vector size is limited with the max-terms option.
            Other options, such as phrase-throughs , will only generate terms if some
            other option is also enabled (in this case fast-phrase-searches ). The
            database options are the same as the database options shown for
            cts:distinctive-terms .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:train
        """
        expr = Cts.train(training_nodes=training_nodes, labels=labels, options=options)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def triple_value_statistics(
        self,
        *,
        values=None,
        forest_ids=None,
        **kwargs,
    ) -> list:
        """Execute ``cts:triple-value-statistics`` via ``/v1/eval``.

        Returns statistics from the triple index for the values given.

        Parameters
        ----------
        values : object
            The values to look up.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:triple-value-statistics
        """
        expr = Cts.triple_value_statistics(values=values, forest_ids=forest_ids)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:triples`` via ``/v1/eval``.

        Returns values from the triple index.

        Parameters
        ----------
        subject : object
            The subjects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        predicate : object
            The predicates to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        object : object
            The objects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        operator : object
            If a single string is provided it is treated as the operator for the $object
            values. If a sequence of three strings are provided, they give the operators
            for $subject, $predicate and $object in turn. The default operator is "=".
            Operators include: "sameTerm" Match triple index values which are the same
            RDF term as $value. This compares aspects of values that are ignored in XML
            Schema comparison semantics, like timezone and derived type of $value. "<"
            Match range index values less than $value. "<=" Match range index values
            less than or equal to $value. ">" Match range index values greater than
            $value. ">=" Match range index values greater than or equal to $value. "="
            Match range index values equal to $value. "!=" Match range index values not
            equal to $value.
        options : object
            Options. The default is (). Options include: "order-pso" Return results
            ordered by predicate, then subject, then object. "order-sop" Return results
            ordered by subject, then object, then predicate. "order-ops" Return results
            ordered by object, then predicate, then subject. "quads" Return quads that
            include values for the named graph that the triples are in. Requires the
            collection lexicon enabled. "any" Values from any fragment should be
            included. "document" Values from document fragments should be included.
            "properties" Values from properties fragments should be included. "locks"
            Values from locks fragments should be included. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "checked" Word positions should be checked when resolving
            the query. "unchecked" Word positions should not be checked when resolving
            the query. "too-many-positions-error" If too much memory is needed to
            perform positions calculations to check whether a document matches a query,
            return an XDMP-TOOMANYPOSITIONS error, instead of accepting the document as
            a match. "eager" Perform work concurrently whilst returning triples from the
            index - buffering some results into memory. This usually takes the shortest
            time when returning a complete result. "lazy" Perform only some the work
            concurrently before returning the first triple from the index, and most of
            the work sequentially while iterating through the rest of the triples. This
            usually takes the shortest time when returning a partial result.
            "concurrent" Perform the work concurrently in another thread. This is a hint
            to the query optimizer to help parallelize the lexicon work, allowing the
            calling query to continue performing other work while the lexicon processing
            occurs. This is especially useful in cases where multiple lexicon calls
            occur in the same query (for example, resolving many facets in a single
            query).
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:triples
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
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:uri-match`` via ``/v1/eval``.

        Returns values from the URI lexicon that match the specified wildcard
        pattern.

        Parameters
        ----------
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" URIs should be returned in
            ascending order. "descending" URIs should be returned in descending order.
            "any" URIs from any fragment should be included. "document" URIs from
            document fragments should be included. "properties" URIs from properties
            fragments should be included. "locks" URIs from locks fragments should be
            included. "frequency-order" URIs should be returned ordered by frequency.
            "item-order" URIs should be returned ordered by item. "limit= N " Return no
            more than N URIs. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the cts:query
            to treat the Nth fragment as the first fragment. URIs from skipped fragments
            are not included. This option affects the number of fragments selected by
            the cts:query to calculate frequencies. Only applies when a $query parameter
            is specified. "sample= N " Return only URIs from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only URIs from
            the first N fragments after skip selected by the cts:query . This option
            also affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[str]
            A list of URI strings; empty when no URIs match.

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
        Native reference: https://docs.marklogic.com/cts:uri-match
        """
        expr = Cts.uri_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ranged(expr, range, index)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_document_patch_path(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-document-patch-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-document-patch-path
        """
        expr = Cts.valid_document_patch_path(string=string, map=map)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_extract_path(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-extract-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-extract-path
        """
        expr = Cts.valid_extract_path(string=string, map=map)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_index_path(self, string, ignorens, **kwargs) -> list:
        """Execute ``cts:valid-index-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces based on the server run-
        time environment.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        ignorens : object
            Ignore namespace prefix binding errors.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-index-path
        """
        expr = Cts.valid_index_path(string=string, ignorens=ignorens)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_optic_path(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-optic-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-optic-path
        """
        expr = Cts.valid_optic_path(string=string, map=map)
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def valid_tde_context(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-tde-context`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-tde-context
        """
        expr = Cts.valid_tde_context(string=string, map=map)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified value lexicon(s).

        Parameters
        ----------
        range_index_1 : object
            A reference to a range index.
        range_index_2 : object
            A reference to a range index.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "timezone=
            TZ " Return timezone sensitive values (dateTime, time, date, gYearMonth,
            gYear, gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. Return only co-occurrences from the
            first N fragments after skip selected by the cts:query , bit do not affect
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the cts:query . This option also affects the number of fragments selected
            by the cts:query to calculate frequencies. Only applies when a $query
            parameter is specified. "score-logtfidf" Compute scores using the logtfidf
            method. Only applies when a $query parameter is specified. "score-logtf"
            Compute scores using the logtf method. Only applies when a $query parameter
            is specified. "score-simple" Compute scores using the simple method. Only
            applies when a $query parameter is specified. "score-random" Compute scores
            using the random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:value-co-occurrences
        """
        expr = Cts.value_co_occurrences(
            range_index_1=range_index_1,
            range_index_2=range_index_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:value-match`` via ``/v1/eval``.

        Returns values from the specified value lexicon(s) that match the
        specified wildcard pattern.

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "timezone= TZ " Return timezone sensitive values (dateTime,
            time, date, gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone
            specified by TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return
            no more than N values. You should not use this option with the "skip"
            option. Use "truncate" instead. "skip= N " Skip over fragments selected by
            the cts:query to treat the Nth fragment as the first fragment. Values from
            skipped fragments are not included. This option affects the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "sample= N " Return only values from
            the first N fragments after skip selected by the cts:query . This option
            does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only values from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence .
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:value-match
        """
        expr = Cts.value_match(
            range_indexes=range_indexes,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified value lexicon(s).

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "timezone= TZ " Return timezone
            sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay)
            adjusted to the timezone specified by TZ . Example timezones: Z, -08:00,
            +01:00. "limit= N " Return no more than N ranges. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:value-ranges
        """
        expr = Cts.value_ranges(
            range_indexes=range_indexes,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:value-tuples`` via ``/v1/eval``.

        Returns value co-occurrence tuples (that is, tuples of values, each of
        which appear in the same fragment) from the specified value lexicons.

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "timezone=
            TZ " Return timezone sensitive values (dateTime, time, date, gYearMonth,
            gYear, gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N tuples. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Co-occurrences from skipped fragments are not included. This
            option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only
            co-occurrences from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:value-tuples
        """
        expr = Cts.value_tuples(
            range_indexes=range_indexes,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:variance`` via ``/v1/eval``.

        Returns a frequency-weighted sample variance given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:variance
        """
        expr = Cts.variance(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:variance-p`` via ``/v1/eval``.

        Returns a frequency-weighted variance of the population given a value
        lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:variance-p
        """
        expr = Cts.variance_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    def walk(self, node, query, expr, **kwargs) -> list:
        """Execute ``cts:walk`` via ``/v1/eval``.

        Walks a node, evaluating an expression with any text matching a query.

        Parameters
        ----------
        node : object
            A node to walk. The node must be either a document node or an element node;
            it cannot be a text node.
        query : object
            A query specifying the text on which to evaluate the expression. If a string
            is entered, the string is treated as a cts:word-query of the specified
            string.
        expr : object
            An expression to evaluate with matching text. You can use the variables
            $cts:text , $cts:node , $cts:queries , $cts:start , and $cts:action
            (described below) in the expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:walk
        """
        expr = Cts.walk(node=node, query=query, expr=expr)
        return self._execute_native(
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
    ) -> list:
        """Execute ``cts:word-match`` via ``/v1/eval``.

        Returns words from the word lexicon that match the wildcard pattern.

        Parameters
        ----------
        pattern : object
            A wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:word-match
        """
        expr = Cts.word_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:words`` via ``/v1/eval``.

        Returns words from the word lexicon.

        Parameters
        ----------
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:words
        """
        expr = Cts.words(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:aggregate`` via ``/v1/eval``.

        Executes a user-defined extension aggregate function against a value
        lexicon or n-way co-occurrence of multiple value lexicons.

        Parameters
        ----------
        native_plugin : object
            The path to the native plugin library containing the implementation of the
            user-defined extension aggregate.
        aggregate_name : object
            The name of an aggregate function in $native-plugin .
        range_indexes : object
            A sequence of references to range indexes. The first range index specified
            in this or any other aggregate function cannot be of type "nullable".
        argument : object
            A sequence containing the arguments for the aggregate function. A map can be
            used to pass in multiple sequences of arguments.
        options : object
            options. The default is (). Options include: "any" Co-occurrences from any
            fragment should be included. "document" Co-occurrences from document
            fragments should be included. "properties" Co-occurrences from properties
            fragments should be included. "locks" Co-occurrences from locks fragments
            should be included. "fragment-frequency" Frequency should be the number of
            fragments with an included co-occurrences. This option is used with
            cts:frequency . "item-frequency" Frequency should be the number of
            occurrences of an included co-occurrence. This option is used with
            cts:frequency . "ordered" Include co-occurrences only when the value from
            the first lexicon appears before the value from the second lexicon. Requires
            that word positions be enabled for both lexicons. "proximity= N " Include
            co-occurrences only when the values appear within N words of each other.
            Requires that word positions be enabled for both lexicons. "checked" Word
            positions should be checked when resolving the query. "unchecked" Word
            positions should not be checked when resolving the query.
            "too-many-positions-error" If too much memory is needed to perform positions
            calculations to check whether a document matches a query, return an
            XDMP-TOOMANYPOSITIONS error, instead of accepting the document as a match.
            "concurrent" Perform the work concurrently in another thread. This is a hint
            to the query optimizer to help parallelize the lexicon work, allowing the
            calling query to continue performing other work while the lexicon processing
            occurs. This is especially useful in cases where multiple lexicon calls
            occur in the same query (for example, resolving many facets in a single
            query).
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:aggregate
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
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:avg-aggregate`` via ``/v1/eval``.

        Returns the average of the values given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:avg-aggregate
        """
        expr = Cts.avg_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:classify`` via ``/v1/eval``.

        Classifies a sequence of nodes based on training data.

        Parameters
        ----------
        data_nodes : object
            The sequence of nodes to be classified.
        classifier : object
            An element node containing the classifier specification. This is typically
            the output of cts:train , either run directly or saved in an XML document in
            the database.
        options : object
            An options element . The options for classification are passed automatically
            from cts:train to the cts:classifier specification as part of the classifier
            element so that they are consistent with the parameters used in training.
            The following option may be separately passed to cts:classify and is in the
            cts:classify namespace . These options override the options present in the
            classifier item-by-item. <thresholds> A definition of the thresholds to use
            in classification. This is a complex element with one or more <threshold>
            children. You can specify both a global value and per-class values (as
            computed from cts:thresholds ). The global value will apply to any classes
            for which a per-class value is not specified. For example: <options
            xmlns="cts:classify"> <thresholds> <threshold>-1.0</threshold> <threshold
            class="Example 1">-2.42</threshold> </thresholds> </options>
        training_nodes : object
            The sequence of training nodes used to train the classifier. Required if the
            supports form of the classifier is used; ignored if the weights form of the
            classifier is used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:classify
        """
        expr = Cts.classify(
            data_nodes=data_nodes,
            classifier=classifier,
            options=options,
            training_nodes=training_nodes,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def cluster(self, nodes, *, options=None, **kwargs) -> list:
        """Execute ``cts:cluster`` via ``/v1/eval``.

        Produces a set of clusters from a sequence of nodes.

        Parameters
        ----------
        nodes : object
            The sequence of nodes to cluster.
        options : object
            An XML representation of the options for defining the clustering parameters.
            The options node must be in the cts:cluster namespace. The following is a
            sample options node: <options xmlns="cts:cluster">
            <label-max-terms>4</label-max-terms> <max-clusters>6</max-clusters>
            <use-db-config>true</use-db-config> </options> The cts:cluster options
            include: < hierarchical-levels > An integer specifying how many hierarchical
            cluster levels the clusterer should return. The default is 1 , which means
            no hierarchical clusters are returned. < label-max-terms > An integer
            specifying the maximum number of terms to use in constructing a cluster
            label. The default is 3 . < label-ignore-words > A space-separated list of
            words that are to be excluded from cluster label. The default is to not
            exclude any words. < label-ignore-attributes > A boolean that indicates
            whether attribute terms should be excluded from the cluster label. The
            default is to include terms from attributes. < details > A boolean that
            indicates whether additional details on the terms used in label generation
            are to be included in the output. See the documentation on
            cts:distinctive-terms for details on the format of the terms returned. The
            default false , meaning no such details are given. < min-clusters > An
            integer specifying a minimum number of desired clusters returned (at any
            hierarchical level). However, if no satisfactory clustering can be produced
            at a given level, only one cluster will be returned, regardless of this
            setting. The default is 3 . < max-clusters > An integer specifying a maximum
            number of clusters that can be returned (at any hierarchical level). The
            default is 15 . < overlapping > A boolean indicating whether it is
            acceptable for nodes to be assigned to more than one cluster. The default is
            false . < max-terms > An integer value specifying the maximum number of
            distinct terms to use in calculating the cluster. The default is 200 .
            Increasing the value will increase the cost (in terms of both time and
            memory) of calculating the clusters, but may improve the quality of the
            clusters. < algorithm > A value indicating which clustering algorithm to
            use, either k-means or lsi . The default is k-means . The LSI algorithm is
            significantly more expensive to compute, both in terms of time and space. <
            num-tries > Specifies the number of times to run the clusterer against the
            specified data. The default is 1. Because of the way the algorithms work,
            running the cluster multiple times will increase the number of terms, and
            tends to improve the accuratacy of the clusters. It does so at the cost of
            performance, as each time it runs, it has to do more work. < use-db-config >
            A boolean value indicating whether to use the current DB configuration for
            determining which terms to use. The default is false , which means that the
            default set of options, as well as any indexing options you specify in the
            options node, will be used for calculating the clusters and their labels.
            When set to true , any indexing options set in the context database
            configuration (including any field settings) are used, as well as any
            default settings that you have not explicitly turned off in the options
            node. The options element also includes indexing options in the
            http://marklogic.com/xdmp/database namespace. These control which terms to
            use. Note that the use of certain options, such as
            fast-case-sensitive-searches , will not impact final results unless the term
            vector size is limited with the max-terms option. Other options, such as
            phrase-throughs , will only generate terms if some other option is also
            enabled (in this case fast-phrase-searches ). The database options are the
            same as the database options shown for cts:distinctive-terms .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:cluster
        """
        expr = Cts.cluster(nodes=nodes, options=options)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:collection-match`` via ``/v1/eval``.

        Returns values from the collection lexicon that match the specified
        wildcard pattern.

        Parameters
        ----------
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" URIs should be returned in
            ascending order. "descending" URIs should be returned in descending order.
            "any" URIs from any fragment should be included. "document" URIs from
            document fragments should be included. "properties" URIs from properties
            fragments should be included. "locks" URIs from locks fragments should be
            included. "frequency-order" URIs should be returned ordered by frequency.
            "item-order" URIs should be returned ordered by item. "limit= N " Return no
            more than N collections. You should not use this option with the "skip"
            option. Use "truncate" instead. "skip= N " Skip over fragments selected by
            the cts:query to treat the Nth fragment as the first fragment. URIs from
            skipped fragments are not included. This option affects the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "sample= N " Return only URIs from the
            first N fragments after skip selected by the cts:query . This option does
            not affect the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only URIs from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:collection-match
        """
        expr = Cts.collection_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:collections`` via ``/v1/eval``.

        Returns values from the collection lexicon.

        Parameters
        ----------
        start : object
            A starting value. Return only this value and following values. If the
            parameter is not in the lexicon, then it returns the values beginning with
            the next value.
        options : object
            Options. The default is (). Options include: "ascending" URIs should be
            returned in ascending order. "descending" URIs should be returned in
            descending order. "any" URIs from any fragment should be included.
            "document" URIs from document fragments should be included. "properties"
            URIs from properties fragments should be included. "locks" URIs from locks
            fragments should be included. "frequency-order" URIs should be returned
            ordered by frequency. "item-order" URIs should be returned ordered by item.
            "limit= N " Return no more than N URIs. You should not use this option with
            the "skip" option. Use "truncate" instead. "skip= N " Skip over fragments
            selected by the cts:query to treat the Nth fragment as the first fragment.
            URIs from skipped fragments are not included. This option affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "sample= N " Return only URIs
            from the first N fragments after skip selected by the cts:query . This
            option does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only URIs from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:collections
        """
        expr = Cts.collections(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def confidence(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:confidence`` via ``/v1/eval``.

        Returns the confidence of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:confidence
        """
        expr = Cts.confidence(node=node)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def contains(self, nodes, query, **kwargs) -> list:
        """Execute ``cts:contains`` via ``/v1/eval``.

        Returns true if any of a sequence of values matches a query.

        Parameters
        ----------
        nodes : object
            The nodes or atomic values to be checked for a match. Atomic values are
            converted to a text node before checking for a match, which may result in an
            error if the value cannot be converted.
        query : object
            A query to match against. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:contains
        """
        expr = Cts.contains(nodes=nodes, query=query)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:correlation`` via ``/v1/eval``.

        Returns the frequency-weighted correlation given a 2-way co-occurrence.

        Parameters
        ----------
        value1 : object
            Reference to a range index. The type of the range index must be numeric.
        value2 : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:correlation
        """
        expr = Cts.correlation(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:count-aggregate`` via ``/v1/eval``.

        Returns the count of a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:count-aggregate
        """
        expr = Cts.count_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:covariance`` via ``/v1/eval``.

        Returns the frequency-weighted sample covariance given a 2-way co-
        occurrence.

        Parameters
        ----------
        value1 : object
            Reference to a range index. The type of the range index must be numeric.
        value2 : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:covariance
        """
        expr = Cts.covariance(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:covariance-p`` via ``/v1/eval``.

        Returns the frequency-weighted covariance of the population given a
        2-way co-occurrence.

        Parameters
        ----------
        value1 : object
            Reference to a range index. The type of the range index must be numeric.
        value2 : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:covariance-p
        """
        expr = Cts.covariance_p(
            value1=value1,
            value2=value2,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def deregister(self, id, **kwargs) -> list:
        """Execute ``cts:deregister`` via ``/v1/eval``.

        Deregister a registered query, explicitly releasing the associated
        resources.

        Parameters
        ----------
        id : object
            A registered query identifier.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:deregister
        """
        expr = Cts.deregister(id=id)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def distinctive_terms(self, nodes, *, options=None, **kwargs) -> list:
        """Execute ``cts:distinctive-terms`` via ``/v1/eval``.

        Return the most "relevant" terms in the model nodes (that is, the terms
        with the highest scores).

        Parameters
        ----------
        nodes : object
            Some model nodes.
        options : object
            An XML representation of the options for defining which terms to generate
            and how to evaluate them. The options node must be in the
            cts:distinctive-terms namespace. The following is a sample options node:
            <options xmlns="cts:distinctive-terms"> <max-terms>20</max-terms> </options>
            The cts:distinctive-terms options (which are also valid for
            cts:similar-query , cts:train , and cts:cluster ) include: < max-terms > An
            integer defining the maximum number of distinctive terms to list in the
            cts:distinctive-terms output. The default is 16. < min-val > A double
            specifying the minimum value a term can have and still be considered a
            distinctive term. The default is 0. < min-weight > A number specifying the
            minimum weighted term frequency a term can have and still be considered a
            distinctive term. In general this value will be either 0 (include unweighted
            terms) or 1 (don't include unweighted terms). The default is 1. < score > A
            string defining which scoring method to use in comparing the values of the
            terms. The default is logtfidf . See the description of scoring methods in
            the cts:search function for more details. Possible values are: logtfidf
            Compute scores using the logtfidf method. logtf Compute scores using the
            logtf method. simple Compute scores using the simple method. < complete > A
            boolean value indicating whether to return terms even if there is no query
            associated with them. The default is false . < use-db-config > The options
            below may be used to easily target a small set of terms. < use-db-config >
            is a boolean value indicating whether to use the currently configured DB
            options as defaults (overriding the built-in ones below) to determine the
            terms to generate. This is true by default. When this is false , any options
            below not explicitly specified take their default values as listed; they do
            not take the database settings' values. Flags explicitly specified override
            defaults, whether built-in (listed below), or from the database
            configuration. Flags not specified in a field apply to all fields, unless
            the field has its own setting, which will be the final value. In other words
            it's a hierarchy, with each more-specific level overriding previous
            less-specific levels. The options element also includes indexing options in
            the http://marklogic.com/xdmp/database namespace. These control which terms
            to use. These database options include the following (shown here with a db
            prefix to denote the http://marklogic.com/xdmp/database namespace . The
            default given below is the default value if use-db-config is set to false :
            < db:word-searches > Include terms for the words in the node. The default is
            false . < db:stemmed-searches > Define whether to include terms for the
            stems in the node, and at what level of stemming: off , basic , advanced ,
            or decompounding . The default is basic . < db:word-positions > Include
            terms for word positions in the node. The default is false . <
            db:fast-case-sensitive-searches > Include terms for case-sensitive
            variations of the words in the node. The default is false . <
            db:fast-diacritic-sensitive-searches > Include terms for diacritic-sensitive
            variations of the words in the node. The default is false . <
            db:fast-phrase-searches > Include terms for two-word phrases in the node.
            The default is true . < db:phrase-throughs > If phrase terms are included,
            include terms for phrases that cross the given elements. The default is to
            have no such elements. Any number can be passed in a single string,
            separated by spaces. < db:phrase-arounds > If phrase terms are included,
            include terms for phrases that skip over the given elements. The default is
            to have no such elements. Any number can be passed in a single string,
            separated by spaces. < db:fast-element-word-searches > Include terms for
            words in particular elements. The default is true . <
            db:fast-element-phrase-searches > Include terms for phrases in particular
            elements. The default is true . < db:element-word-positions > Include terms
            for element word positions in the node. The default is false . <
            db:element-word-query-throughs > Include terms for words in sub-elements of
            the given elements. The default is to have no such elements. Any number can
            be passed in a single string, separated by spaces. <
            db:fast-element-character-searches > Include terms for characters in
            particular elements. The default is false . < db:range-element-indexes >
            Include terms for data values in specific elements. The default is to have
            no such indexes. < db:range-field-indexes > Include terms for data values in
            specific fields. The default is to have no such indexes. <
            db:range-element-attribute-indexes > Include terms for data values in
            specific attributes. The default is to have no such indexes. <
            db:one-character-searches > Include terms for single character. The default
            is false . < db:two-character-searches > Include terms for two-character
            sequences. The default is false . < db:three-character-searches > Include
            terms three-character sequences. The default is false . <
            db:trailing-wildcard-searches > Include terms for trailing wildcards. The
            default is false . < db:fast-element-trailing-wildcard-searches > If
            trailing wildcard terms are included, include terms for trailing wildcards
            by element. The default is false . < db:fields > Include terms for the
            defined fields. The default is to have no fields.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:distinctive-terms
        """
        expr = Cts.distinctive_terms(nodes=nodes, options=options)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-attribute-pair-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : object
            One or more element QNames.
        latitude_names : object
            One or more element QNames.
        longitude_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Build an ``element-attribute-pair-geospatial-value-match`` call.

        Returns values from the specified element attribute pair geospatial
        value lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-pair-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element-attribute-pair geospatial
        value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences from the specified element or element-
        attribute value lexicon(s).

        Parameters
        ----------
        element_name_1 : object
            An element QName.
        attribute_name_1 : object
            An attribute QName or empty sequence. The empty sequence specifies an
            element lexicon.
        element_name_2 : object
            An element QName.
        attribute_name_2 : object
            An attribute QName or empty sequence. The empty sequence specifies an
            element lexicon.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For both lexicons, use the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "type-1= type " For the first lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the second lexicon, use the type
            specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " For
            both lexicons, use the collation specified by URI . "collation-1= URI " For
            the first lexicon, use the collation specified by URI . "collation-2= URI "
            For the second lexicon, use the collation specified by URI . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only
            co-occurrences from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence . "coordinate-system= name " Use the
            lexicon that is configured with the specified coordinate system. Allowed
            values: "wgs84", "wgs84/double", "raw", "raw/double". Only applicable if the
            lexicon value type is point or long-lat-point . "precision= value " Use the
            lexicon that is configured with the specified precision. Allowed values:
            float and double . Only applicable if the lexicon value type is point or
            long-lat-point . This value takes precedence over the precision implicit in
            the coordinate system name.
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference:
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
        return await self._execute_native(
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
    ) -> list:
        """Build an ``element-attribute-value-geospatial-co-occurrences`` call.

        Returns value co-occurrences from the specified element-attribute value
        lexicon with the specified geospatial lexicon.

        Parameters
        ----------
        element_name_1 : object
            A QName identifying the parent element of the first lexicon.
        attribute_name_1 : object
            A QName identifying an attribute of element-name-1 .
        geo_element_name : object
            A QName identifying the second lexicon, which must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the coord-child-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in coord-child-name-1 and coord-child-name-2 .
        coord_child_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name identifies an element or JSON property
            geospatial lexicon.
        coord_child_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : object
            Options. The default is (). The following options are available:
            "geospatial-format= format " Use the kind of geospatial lexicon specified by
            format (element, element-child, element-pair, or element-attribute-pair). If
            neither of the child QNames is specified, the default is "element"; if only
            the first of the child QNames is specified, the default is "element-child:;
            if both child QNames are specified, the default is "element-pair". If the
            selection is not compatible with the number of geospatial QNames specified,
            an error is raised. "ascending" Co-occurrences should be returned in
            ascending order. "descending" Co-occurrences should be returned in
            descending order. "any" Co-occurrences from any fragment should be included.
            "document" Co-occurrences from document fragments should be included.
            "properties" Co-occurrences from properties fragments should be included.
            "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For the non-geospatial lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "collation= URI " For the non-geospatial lexicon, use the
            collation specified by URI . "coordinate-system= name " For the geospatial
            lexicons, use the coordinate system specified by name . Allowed values:
            "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double".
            "precision= value " Use the coordinate system at the given precision.
            Allowed values: float and double . "timezone= TZ " Return timezone sensitive
            values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay) adjusted
            to the timezone specified by TZ . Example timezones: Z, -08:00, +01:00.
            "ordered" Include co-occurrences only when the value from the first lexicon
            appears before the value from the second lexicon. Requires that word
            positions be enabled for both lexicons. "reversed" Consider the second
            lexicon as the first and vice versa. "proximity= N " Include co-occurrences
            only when the values appear within N words of each other. Requires that word
            positions be enabled for both lexicons. "limit= N " Return no more than N
            co-occurrences. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Co-occurrences from
            skipped fragments are not included. This option affects the number of
            fragments selected by the query to calculate frequencies. Only applies when
            a $query parameter is specified. "sample= N " Return only co-occurrences
            from the first N fragments after skip selected by the query . This option
            does not affect the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the query . This option affects the number of fragments selected by the
            query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference:
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
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-attribute-value-match`` via ``/v1/eval``.

        Returns values from the specified element-attribute value lexicon(s)
        that match the specified pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "item-order" Values should be returned ordered by item.
            "type= type " Use the lexicon with the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "collation= URI " Use the range index with the collation
            specified by URI . "timezone= TZ " Return timezone sensitive values
            (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay) adjusted to the
            timezone specified by TZ . Example timezones: Z, -08:00, +01:00. "limit= N "
            Return no more than N values. You should not use this option with the "skip"
            option. Use "truncate" instead. "skip= N " Skip over fragments selected by
            the cts:query to treat the Nth fragment as the first fragment. Values from
            skipped fragments are not included. This option affects the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "sample= N " Return only values from
            the first N fragments after skip selected by the cts:query . This option
            does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only values from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-value-match
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified element-attribute value
        lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "type= type " Use the lexicon with the
            type specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " Use
            the range index with the collation specified by URI . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "limit= N " Return no more than N ranges. You should not use
            this option with the "skip" option. Use "truncate" instead. "skip= N " Skip
            over fragments selected by the cts:query to treat the Nth fragment as the
            first fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentiallya while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
            "coordinate-system= name " Use the lexicon that is configured with the
            specified coordinate system. Allowed values: "wgs84", "wgs84/double", "raw",
            "raw/double". Only applicable if the lexicon value type is point or
            long-lat-point . "precision= value " Use the lexicon that is configured with
            the specified precision. Allowed values: float and double . Only applicable
            if the lexicon value type is point or long-lat-point . This value takes
            precedence over the precision implicit in the coordinate system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-value-ranges
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
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-attribute-values`` via ``/v1/eval``.

        Returns values from the specified element-attribute value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "type= type " Use
            the lexicon with the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "collation= URI " Use the range index with the collation specified by URI .
            "timezone= TZ " Return timezone sensitive values (dateTime, time, date,
            gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone specified by
            TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return no more than N
            values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the cts:query
            to treat the Nth fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "sample= N " Return only values from the
            first N fragments after skip selected by the cts:query . This option does
            not affect the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only values from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-values
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-word-match`` via ``/v1/eval``.

        Returns words from the specified element-attribute word lexicon(s) that
        match a wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-word-match
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-attribute-words`` via ``/v1/eval``.

        Returns words from the specified element-attribute word lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        attribute_names : object
            One or more attribute QNames.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-attribute-words
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-child-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : object
            One or more element QNames.
        child_element_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-child-geospatial-value-match`` via ``/v1/eval``.

        Returns values from the specified element child geospatial value
        lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames identifying the parent element(s).
        child_names : object
            One or more child element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-child-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element-child geospatial value
        lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        child_names : object
            One or more child element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "score-zero" Compute all scores as zero. "checked"
            Word positions should be checked when resolving the query. "unchecked" Word
            positions should not be checked when resolving the query.
            "too-many-positions-error" If too much memory is needed to perform positions
            calculations to check whether a document matches a query, return an
            XDMP-TOOMANYPOSITIONS error, instead of accepting the document as a match.
            "eager" Perform most of the work concurrently before returning the first
            item from the indexes, and only some of the work sequentially while
            iterating through the rest of the items. This usually takes the shortest
            time for a complete item-order result or for any frequency-order result.
            "lazy" Perform only some the work concurrently before returning the first
            item from the indexes, and most of the work sequentially while iterating
            through the rest of the items. This usually takes the shortest time for a
            small item-order partial result. "concurrent" Perform the work concurrently
            in another thread. This is a hint to the query optimizer to help parallelize
            the lexicon work, allowing the calling query to continue performing other
            work while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-values
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Use the following options to customize your lexicon query: "ascending" Boxes
            should be returned in ascending order. "descending" Boxes should be returned
            in descending order. "gridded" For each side that a bucket is bounded,
            return the corresponding bound as the edge of the box, instead of the
            extremum from the points in the bucket. "empties" Include fully-bounded
            ranges whose frequency is 0. Only empty ranges that have both their upper
            and lower bounds specified in the $bounds options are returned; any empty
            ranges that are less than the first bound or greater than the last bound are
            not returned. For example, if you specify 4 bounds and there are no results
            for any of the bounds, 3 elements are returned (not 5 elements). "any"
            Points from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon that is
            configured with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-geospatial-value-match`` via ``/v1/eval``.

        Returns values from the specified element geospatial value lexicon(s)
        that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-geospatial-value-match
        """
        expr = Cts.element_geospatial_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element geospatial value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-geospatial-values
        """
        expr = Cts.element_geospatial_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-pair-geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : object
            One or more element QNames.
        latitude_names : object
            One or more element QNames.
        longitude_names : object
            One or more element QNames.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-pair-geospatial-value-match`` via ``/v1/eval``.

        Returns values from the specified element pair geospatial value
        lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference:
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-pair-geospatial-values`` via ``/v1/eval``.

        Returns values from the specified element-pair geospatial value
        lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames identifying the parent element of the latitude
            and longitude elements.
        latitude_names : object
            One or more latitude element QNames.
        longitude_names : object
            One or more longitude element QNames.
        start : object
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "coordinate-system=
            name " Use the lexicon with the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "limit= N " Return no more
            than N values. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Values from skipped
            fragments are not included. This option affects the number of fragments
            selected by the query to calculate frequencies. Only applies when a $query
            parameter is specified. "sample= N " Return only values from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            values from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:point* sequence .
        query : object
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-values
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified element value
        lexicon(s).

        Parameters
        ----------
        element_name_1 : object
            An element QName.
        element_name_2 : object
            An element QName.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For both lexicons, use the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "type-1= type " For the first lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the second lexicon, use the type
            specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " For
            both lexicons, use the collation specified by URI . "collation-1= URI " For
            the first lexicon, use the collation specified by URI . "collation-2= URI "
            For the second lexicon, use the collation specified by URI . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only
            co-occurrences from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence . "coordinate-system= name " Use
            lexicons configured with the specified coordinate system. Allowed values:
            "wgs84", "wgs84/double", "raw", "raw/double". Only applicable if the lexicon
            value type is point or long-lat-point . "precision= value " Use lexicons
            configured with the specified precision. Allowed values: float and double .
            Only applicable if the lexicon value type is point or long-lat-point . This
            value takes precedence over the precision implicit in the coordinate system
            name.
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-value-co-occurrences
        """
        expr = Cts.element_value_co_occurrences(
            element_name_1=element_name_1,
            element_name_2=element_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-value-geospatial-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences from the specified element value lexicon
        with the specified geospatial lexicon.

        Parameters
        ----------
        element_name_1 : object
            A QName identifying the first lexicon. If this is a geospatial lexicon, it
            can only be an element geospatial lexicon. You should usually use
            cts:geospatial-co-occurrences to find co-occurrences between two geospatial
            lexicons.
        geo_element_name : object
            A QName identifying the second lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the coord-child-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in coord-child-name-1 and coord-child-name-2 .
        coord_child_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name identifies an element or JSON property
            geospatial lexicon.
        coord_child_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : object
            Options. The default is (). The following options are available:
            "geospatial-format= format " Use the kind of geospatial lexicon specified by
            format (element, element-child, element-pair, or element-attribute-pair). If
            neither of the child QNames is specified, the default is "element"; if only
            the first of the child QNames is specified, the default is "element-child:;
            if both child QNames are specified, the default is "element-pair". If the
            selection is not compatible with the number of geospatial QNames specified,
            an error is raised. "ascending" Co-occurrences should be returned in
            ascending order. "descending" Co-occurrences should be returned in
            descending order. "any" Co-occurrences from any fragment should be included.
            "document" Co-occurrences from document fragments should be included.
            "properties" Co-occurrences from properties fragments should be included.
            "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For the non-geospatial lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the geospatial lexicon, use the type
            specified by type-2 (point or long-lat-point) "collation= URI " For the
            non-geospatial lexicon, use the collation specified by URI .
            "coordinate-system= name " Use the coordinate system specified by name .
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "ordered" Include co-occurrences only when the value from
            the first lexicon appears before the value from the second lexicon. Requires
            that word positions be enabled for both lexicons. "reversed" Consider the
            second lexicon as the first and vice versa. "proximity= N " Include
            co-occurrences only when the values appear within N words of each other.
            Requires that word positions be enabled for both lexicons. "limit= N "
            Return no more than N co-occurrences. You should not use this option with
            the "skip" option. Use "truncate" instead. "skip= N " Skip over fragments
            selected by the query to treat the Nth matching fragment as the first
            fragment. Co-occurrences from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only co-occurrences from the first N fragments after skip selected by
            the query . This option does not affect the number of fragments selected by
            the query to calculate frequencies. Only applies when a $query parameter is
            specified. "truncate= N " Include only co-occurrences from the first N
            fragments after skip selected by the query . This option affects the number
            of fragments selected by the query to calculate frequencies. Only applies
            when a $query parameter is specified. "score-logtfidf" Compute scores using
            the logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference:
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
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-value-match`` via ``/v1/eval``.

        Returns values from the specified element value lexicon(s) that match
        the specified wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "type= type " Use the lexicon with the type specified by
            type (int, unsignedInt, long, unsignedLong, float, double, decimal,
            dateTime, time, date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration,
            dayTimeDuration, string, or anyURI) "collation= URI " Use the range index
            with the collation specified by URI . "timezone= TZ " Return timezone
            sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay)
            adjusted to the timezone specified by TZ . Example timezones: Z, -08:00,
            +01:00. "limit= N " Return no more than N values. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only values from the first N fragments after skip selected by the
            cts:query . This option does not affect the number of fragments selected by
            the cts:query to calculate frequencies. Only applies when a $query parameter
            is specified. "truncate= N " Include only values from the first N fragments
            after skip selected by the cts:query . This option also affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "score-logtfidf" Compute
            scores using the logtfidf method. Only applies when a $query parameter is
            specified. "score-logtf" Compute scores using the logtf method. Only applies
            when a $query parameter is specified. "score-simple" Compute scores using
            the simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-value-match
        """
        expr = Cts.element_value_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified element value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "type= type " Use the lexicon with the
            type specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " Use
            the lexicon with the collation specified by URI . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "limit= N " Return no more than N ranges. You should not use
            this option with the "skip" option. Use "truncate" instead. "skip= N " Skip
            over fragments selected by the cts:query to treat the Nth fragment as the
            first fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
            "coordinate-system= name " Use the lexicon that is configured with the
            specified coordinate system. Allowed values: "wgs84", "wgs84/double", "raw",
            "raw/double". Only applicable if the lexicon value type is point or
            long-lat-point . "precision= value " Use the lexicon that is configured with
            the specified precision. Allowed values: float and double . Only applicable
            if the lexicon value type is point or long-lat-point . This value takes
            precedence over the precision implicit in the coordinate system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-value-ranges
        """
        expr = Cts.element_value_ranges(
            element_names=element_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-values`` via ``/v1/eval``.

        Returns values from the specified element value lexicon(s).

        Parameters
        ----------
        element_names : object
            One or more element QNames. If you specify multiple lexicons, they must all
            be over the same value type (string, int, etc.).
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "type= type " Use
            the lexicon with the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "collation= URI " Use the lexicon with the collation specified by URI .
            "timezone= TZ " Return timezone sensitive values (dateTime, time, date,
            gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone specified by
            TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return no more than N
            words. You should not use this option with the "skip" option. Use "truncate"
            instead. "skip= N " Skip over fragments selected by the cts:query to treat
            the Nth fragment as the first fragment. Values from skipped fragments are
            not included. This option affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "sample= N " Return only values from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only values
            from the first N fragments after skip selected by the cts:query . This
            option also affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-values
        """
        expr = Cts.element_values(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def element_walk(self, node, element, expr, **kwargs) -> list:
        """Execute ``cts:element-walk`` via ``/v1/eval``.

        Returns a copy of the node, replacing any elements found with the
        specified expression.

        Parameters
        ----------
        node : object
            A node to run the walk over. The node must be either a document node or an
            element node; it cannot be a text node.
        element : object
            The name of elements to replace.
        expr : object
            An expression with which to replace each match. You can use the variables
            $cts:node and $cts:action (described below) in the expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:element-walk
        """
        expr = Cts.element_walk(node=node, element=element, expr=expr)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:element-word-match`` via ``/v1/eval``.

        Returns words from the specified element word lexicon(s) that match a
        wildcard pattern.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-word-match
        """
        expr = Cts.element_word_match(
            element_names=element_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:element-words`` via ``/v1/eval``.

        Returns words from the specified element word lexicon.

        Parameters
        ----------
        element_names : object
            One or more element QNames.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:element-words
        """
        expr = Cts.element_words(
            element_names=element_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def entity_dictionary_get(self, uri, **kwargs) -> list:
        """Execute ``cts:entity-dictionary-get`` via ``/v1/eval``.

        Retrieve an entity dictionary previously cached in the database.

        Parameters
        ----------
        uri : object
            URI of a previously saved entity dictionary.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:entity-dictionary-get
        """
        expr = Cts.entity_dictionary_get(uri=uri)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def entity_highlight(self, node, expr, *, dict=None, **kwargs) -> list:
        """Execute ``cts:entity-highlight`` via ``/v1/eval``.

        Returns a copy of the node, replacing any entities found with the
        specified expression.

        Parameters
        ----------
        node : object
            A node to run entity highlight on. The node must be either a document node
            or an element node; it cannot be a text node.
        expr : object
            An expression with which to replace each match. You can use the variables
            $cts:text , $cts:node , $cts:entity-type and $cts:normalized-text ,
            $cts:start , and $cts:action (described below) in the expression.
        dict : object
            The entity dictionary to use for matching entities in the text of the input
            node. If you omit this parameter, the default entity dictionary is used. (No
            default dictionaries currently exist.) See the Usage Notes for details.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:entity-highlight
        """
        expr = Cts.entity_highlight(node=node, expr=expr, dict=dict)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def entity_walk(self, node, expr, *, dict=None, **kwargs) -> list:
        """Execute ``cts:entity-walk`` via ``/v1/eval``.

        Walk an XML document or element node, evaluating an expression against
        any matching entities.

        Parameters
        ----------
        node : object
            A node to walk. The node must be either an XML document node or an XML
            element node; it cannot be a text node.
        expr : object
            An expression to evaluate for each match. You can use the variables
            $cts:text , $cts:node , $cts:entity-type , $cts:normalized-text ,
            $cts:entity-id , $cts:start , and $cts:action in the expression. See the
            Usage Notes for details.
        dict : object
            The entity dictionary to use for matching entities in the text of the input
            node. If you omit this parameter, the default entity dictionary is used. (No
            default dictionaries currently exist.) See the Usage Notes for details.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:entity-walk
        """
        expr = Cts.entity_walk(node=node, expr=expr, dict=dict)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:field-value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified field value lexicon(s).

        Parameters
        ----------
        field_name_1 : object
            A string.
        field_name_2 : object
            A string.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "type= type
            " For both lexicons, use the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "type-1= type " For the first lexicon, use the type specified by type (int,
            unsignedInt, long, unsignedLong, float, double, decimal, dateTime, time,
            date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration,
            string, or anyURI) "type-2= type " For the second lexicon, use the type
            specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " For
            both lexicons, use the collation specified by URI . "collation-1= URI " For
            the first lexicon, use the collation specified by URI . "collation-2= URI "
            For the second lexicon, use the collation specified by URI . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. Return only co-occurrences from the
            first N fragments after skip selected by the cts:query , bit do not affect
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the cts:query . This option also affects the number of fragments selected
            by the cts:query to calculate frequencies. Only applies when a $query
            parameter is specified. "score-logtfidf" Compute scores using the logtfidf
            method. Only applies when a $query parameter is specified. "score-logtf"
            Compute scores using the logtf method. Only applies when a $query parameter
            is specified. "score-simple" Compute scores using the simple method. Only
            applies when a $query parameter is specified. "score-random" Compute scores
            using the random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence . "coordinate-system= name " Use the
            lexicon that is configured with the specified coordinate system. Allowed
            values: "wgs84", "wgs84/double", "raw", "raw/double". Only applicable if the
            lexicon value type is point or long-lat-point . "precision= value " Use the
            lexicon that is configured with the specified precision. Allowed values:
            float and double . Only applicable if the lexicon value type is point or
            long-lat-point . This value takes precedence over the precision implicit in
            the coordinate system name.
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:field-value-co-occurrences
        """
        expr = Cts.field_value_co_occurrences(
            field_name_1=field_name_1,
            field_name_2=field_name_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:field-value-match`` via ``/v1/eval``.

        Returns values from the specified field value lexicon(s) that match the
        specified wildcard pattern.

        Parameters
        ----------
        field_names : object
            One or more field names.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "type= type " Use the lexicon with the type specified by
            type (int, unsignedInt, long, unsignedLong, float, double, decimal,
            dateTime, time, date, gYearMonth, gYear, gMonth, gDay, yearMonthDuration,
            dayTimeDuration, string, or anyURI) "collation= URI " Use the range index
            with the collation specified by URI . "timezone= TZ " Return timezone
            sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay)
            adjusted to the timezone specified by TZ . Example timezones: Z, -08:00,
            +01:00. "limit= N " Return no more than N values. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only values from the first N fragments after skip selected by the
            cts:query . This option does not affect the number of fragments selected by
            the cts:query to calculate frequencies. Only applies when a $query parameter
            is specified. "truncate= N " Include only values from the first N fragments
            after skip selected by the cts:query . This option also affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "score-logtfidf" Compute
            scores using the logtfidf method. Only applies when a $query parameter is
            specified. "score-logtf" Compute scores using the logtf method. Only applies
            when a $query parameter is specified. "score-simple" Compute scores using
            the simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence . "coordinate-system= name " Use the lexicon that is configured
            with the specified coordinate system. Allowed values: "wgs84",
            "wgs84/double", "raw", "raw/double". Only applicable if the lexicon value
            type is point or long-lat-point . "precision= value " Use the lexicon that
            is configured with the specified precision. Allowed values: float and double
            . Only applicable if the lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-value-match
        """
        expr = Cts.field_value_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:field-value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified field value lexicon(s).

        Parameters
        ----------
        field_names : object
            One or more element QNames.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "type= type " Use the lexicon with the
            type specified by type (int, unsignedInt, long, unsignedLong, float, double,
            decimal, dateTime, time, date, gYearMonth, gYear, gMonth, gDay,
            yearMonthDuration, dayTimeDuration, string, or anyURI) "collation= URI " Use
            the lexicon with the collation specified by URI . "timezone= TZ " Return
            timezone sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth,
            and gDay) adjusted to the timezone specified by TZ . Example timezones: Z,
            -08:00, +01:00. "limit= N " Return no more than N ranges. You should not use
            this option with the "skip" option. Use "truncate" instead. "skip= N " Skip
            over fragments selected by the cts:query to treat the Nth fragment as the
            first fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
            "coordinate-system= name " Use the lexicon that is configured with the
            specified coordinate system. Allowed values: "wgs84", "wgs84/double", "raw",
            "raw/double". Only applicable if the lexicon value type is point or
            long-lat-point . "precision= value " Use the lexicon that is configured with
            the specified precision. Allowed values: float and double . Only applicable
            if the lexicon value type is point or long-lat-point . This value takes
            precedence over the precision implicit in the coordinate system name.
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:field-value-ranges
        """
        expr = Cts.field_value_ranges(
            field_names=field_names,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:field-values`` via ``/v1/eval``.

        Returns values from the specified field value lexicon(s).

        Parameters
        ----------
        field_names : object
            One or more field names.
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "type= type " Use
            the lexicon with the type specified by type (int, unsignedInt, long,
            unsignedLong, float, double, decimal, dateTime, time, date, gYearMonth,
            gYear, gMonth, gDay, yearMonthDuration, dayTimeDuration, string, or anyURI)
            "collation= URI " Use the lexicon with the collation specified by URI .
            "timezone= TZ " Return timezone sensitive values (dateTime, time, date,
            gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone specified by
            TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return no more than N
            words. You should not use this option with the "skip" option. Use "truncate"
            instead. "skip= N " Skip over fragments selected by the cts:query to treat
            the Nth fragment as the first fragment. Values from skipped fragments are
            not included. This option affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "sample= N " Return only values from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only values
            from the first N fragments after skip selected by the cts:query . This
            option also affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence .
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-values
        """
        expr = Cts.field_values(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:field-word-match`` via ``/v1/eval``.

        Returns words from the specified field word lexicon(s) that match a
        wildcard pattern.

        Parameters
        ----------
        field_names : object
            One or more field names.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth matching fragment as
            the first fragment. Words from skipped fragments are not included. Only
            applies when a $query parameter is specified. "sample= N " Return only words
            from the first N fragments after skip selected by the cts:query . Only
            applies when a $query parameter is specified. "truncate= N " Include only
            words from the first N fragments after skip selected by the cts:query . Only
            applies when a $query parameter is specified. "score-logtfidf" Compute
            scores using the logtfidf method. Only applies when a $query parameter is
            specified. "score-logtf" Compute scores using the logtf method. Only applies
            when a $query parameter is specified. "score-simple" Compute scores using
            the simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-word-match
        """
        expr = Cts.field_word_match(
            field_names=field_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:field-words`` via ``/v1/eval``.

        Returns words from the specified field word lexicon.

        Parameters
        ----------
        field_names : object
            One or more field names.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:field-words
        """
        expr = Cts.field_words(
            field_names=field_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
        return await self._execute(
            expr,
            ValueHit,
            **_execution_options(self._namespaces, kwargs),
        )

    async def fitness(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:fitness`` via ``/v1/eval``.

        Returns the fitness of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:fitness
        """
        expr = Cts.fitness(node=node)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def frequency(self, value, **kwargs) -> list:
        """Execute ``cts:frequency`` via ``/v1/eval``.

        Returns an integer representing the number of times in which a
        particular value occurs in a value lexicon lookup.

        Parameters
        ----------
        value : object
            A value from a lexicon lookup function. For example, a value returned by a
            function such as cts:values , cts:words , cts:field-values ,
            cts:field-word-match , or cts:geospatial-boxes .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:frequency
        """
        expr = Cts.frequency(value=value)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:geospatial-boxes`` via ``/v1/eval``.

        Returns boxes derived from the specified point lexicon(s).

        Parameters
        ----------
        geo_indexes : object
            A sequence of references to geospatial indexes.
        latitude_bounds : object
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : object
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : object
            Options. The default is (). Options include: "ascending" Boxes should be
            returned in ascending order. "descending" Boxes should be returned in
            descending order. "gridded" For each side that a bucket is bounded, return
            the corresponding bound as the edge of the box, instead of the extremum from
            the points in the bucket. "empties" Include fully-bounded ranges whose
            frequency is 0. Only empty ranges that have both their upper and lower
            bounds specified in the $bounds options are returned; any empty ranges that
            are less than the first bound or greater than the last bound are not
            returned. For example, if you specify 4 bounds and there are no results for
            any of the bounds, 3 elements are returned (not 5 elements). "any" Points
            from any fragment should be included. "document" Points from document
            fragments should be included. "properties" Points from properties fragments
            should be included. "locks" Points from locks fragments should be included.
            "frequency-order" Boxes should be returned ordered by frequency.
            "item-order" Boxes should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included point. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included point. This option is used with
            cts:frequency . "coordinate-system= name " Use the lexicon with the
            coordinate system specified by name . Allowed values: "wgs84",
            "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double". "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . "limit= N " Return no more than N boxes. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the query to treat the Nth matching fragment
            as the first fragment. Points from skipped fragments are not included. This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only boxes for buckets with at least one point from the first N
            fragments after skip selected by the query . This option does not affect the
            number of fragments selected by the query to calculate frequencies. Only
            applies when a $query parameter is specified. "truncate= N " Include only
            points from the first N fragments after skip selected by the query . This
            option affects the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "type=long-lat-point" Specifies the format for the point in the data as
            longitude first, latitude second. "type=point" Specifies the format for the
            point in the data as latitude first, longitude second. This is the default
            format. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a cts:box* sequence .
        query : object
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:geospatial-boxes
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
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:geospatial-co-occurrences`` via ``/v1/eval``.

        Find value co-occurrences from two geospatial lexicons.

        Parameters
        ----------
        geo_element_name_1 : object
            A QName identifying the first lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the child-1-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in child-1-name-1 and child-1-name-2 .
        geo_element_name_2 : object
            A QName identifying the first lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the child-2-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in child-2-name-1 and child-2-name-2 .
        child_1_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-1 that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name-1 identifies an element or JSON property
            geospatial lexicon.
        child_1_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-1 that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        child_2_name_1 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-2 that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name-2 identifies an element or JSON property
            geospatial lexicon.
        child_2_name_2 : object
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-2 that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : object
            Options. The default is (). The following options are available:
            "geospatial-format= format " For both geospatial lexicons, use the kind of
            geospatial lexicon specified by format (element, element-child,
            element-pair, or element-attribute-pair). If neither of the child QNames is
            specified, the default is "element"; if only the first of the child QNames
            is specified, the default is "element-child:; if both child QNames are
            specified, the default is "element-pair". If the selection is not compatible
            with the number of geospatial QNames specified, an error is raised.
            "geospatial-format-1= format " For the first geospatial lexicon, use the
            kind of geospatial lexicon specified by format (element, element-child,
            element-pair, or element-attribute-pair). If neither of the child QNames is
            specified, the default is "element"; if only the first of the child QNames
            is specified, the default is "element-child:; if both child QNames are
            specified, the default is "element-pair". If the selection is not compatible
            with the number of geospatial QNames specified, an error is raised.
            "geospatial-format-2= format " For the second geospatial lexicons, use the
            kind of geospatial lexicon specified by format (element, element-child,
            element-pair, or element-attribute-pair). If neither of the child QNames is
            specified, the default is "element"; if only the first of the child QNames
            is specified, the default is "element-child:; if both child QNames are
            specified, the default is "element-pair". If the selection is not compatible
            with the number of geospatial QNames specified, an error is raised.
            "ascending" Co-occurrences should be returned in ascending order.
            "descending" Co-occurrences should be returned in descending order. "any"
            Co-occurrences from any fragment should be included. "document"
            Co-occurrences from document fragments should be included. "properties"
            Co-occurrences from properties fragments should be included. "locks"
            Co-occurrences from locks fragments should be included. "frequency-order"
            Co-occurrences should be returned ordered by frequency. "item-order"
            Co-occurrences should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included co-occurrences.
            This option is used with cts:frequency . "item-frequency" Frequency should
            be the number of occurrences of an included co-occurrence. This option is
            used with cts:frequency . "coordinate-system= name " For both geospatial
            lexicons, use the coordinate system specified by name . Allowed values:
            "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw", "raw/double".
            "coordinate-system-1= string " For the first geospatial lexicon, use the
            coordinate system specified by name . "coordinate-system-2= string " For the
            second geospatial lexicons, use the coordinate system specified by name .
            "ordered" Include co-occurrences only when the value from the first lexicon
            appears before the value from the second lexicon. Requires that word
            positions be enabled for both lexicons. "reversed" Consider the second
            lexicon as the first and vice versa. "proximity= N " Include co-occurrences
            only when the values appear within N words of each other. Requires that word
            positions be enabled for both lexicons. "limit= N " Return no more than N
            co-occurrences. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the query to
            treat the Nth matching fragment as the first fragment. Co-occurrences from
            skipped fragments are not included. This option affects the number of
            fragments selected by the query to calculate frequencies. Only applies when
            a $query parameter is specified. "sample= N " Return only co-occurrences
            from the first N fragments after skip selected by the query . This option
            does not affect the number of fragments selected by the query to calculate
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the query . This option affects the number of fragments selected by the
            query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as a
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:geospatial-co-occurrences
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
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def highlight(self, node, query, expr, **kwargs) -> list:
        """Execute ``cts:highlight`` via ``/v1/eval``.

        Returns a copy of the node, replacing any text matching the query with
        the specified expression.

        Parameters
        ----------
        node : object
            A node to highlight. The node must be either a document node or an element
            node; it cannot be a text node.
        query : object
            A query specifying the text to highlight. If a string is entered, the string
            is treated as a cts:word-query of the specified string.
        expr : object
            An expression with which to replace each match. You can use the variables
            $cts:text , $cts:node , $cts:queries , $cts:start , and $cts:action
            (described below) in the expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:highlight
        """
        expr = Cts.highlight(node=node, query=query, expr=expr)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:json-property-word-match`` via ``/v1/eval``.

        Returns words from the specified JSON property word lexicon(s) that
        match a wildcard pattern.

        Parameters
        ----------
        property_names : object
            One or more property names.
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:json-property-word-match
        """
        expr = Cts.json_property_word_match(
            property_names=property_names,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:json-property-words`` via ``/v1/eval``.

        Returns words from the specified JSON property word lexicon.

        Parameters
        ----------
        property_names : object
            One or more property names.
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:json-property-words
        """
        expr = Cts.json_property_words(
            property_names=property_names,
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:linear-model`` via ``/v1/eval``.

        Returns a linear model that fits the frequency-weighted data set.

        Parameters
        ----------
        values : object
            References to two range indexes. The types of the range indexes must be
            numeric. If the size of this sequence is not 2, the function returns the
            empty sequence.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:linear-model
        """
        expr = Cts.linear_model(
            values=values,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:match-regions`` via ``/v1/eval``.

        Find regions in documents that have a spatial relationship to one or
        more caller-supplied regions.

        Parameters
        ----------
        range_indexes : object
            References to range indexes that store the string serialization of regions
            to match against.
        operation : object
            The operation to test. Must be one of the following: contains , covered-by ,
            covers , crosses , disjoint , equals , intersects , overlaps , touches ,
            within . See the Usage Notes for details.
        regions : object
            One or more cts:region values to test against. A region matches if it
            matches against any of these regions.
        options : object
            String options you can use to control the operation. The following options
            are supported: "coordinate-system= value " Use the given coordinate system.
            Valid values are wgs84 , wgs84/double , etrs89 , etrs89/double , raw and
            raw/double . Defaults to the governing coordinating system. "precision=
            value " Use the coordinate system at the given precision. Allowed values:
            float and double . Defaults to the precision of the governing coordinate
            system. "units= value " Compute distances and radii of circles using the
            given units. Allowed values: miles (default), km , feet , and meters .
            "strings" Return results as strings instead of as cts:region values. "any"
            Co-occurrences from any fragment should be included. "document"
            Co-occurrences from document fragments should be included. "properties"
            Co-occurrences from properties fragments should be included. "locks"
            Co-occurrences from locks fragments should be included. "fragment-frequency"
            Frequency should be the number of fragments with an included co-occurrence.
            This option is used with cts:frequency . "item-frequency" Frequency should
            be the number of occurrences of an included co-occurrence. This option is
            used with cts:frequency . "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query).
        query : object
            Limit the region comparison to documents that match this query. Also,
            compute frequencies from the set of included regions. The values do not need
            to match the query, but they must occur in fragments selected by the query.
            The fragments are not filtered to ensure they match the query. Instead, they
            are selected in the same manner as "unfiltered" cts:search operations.
        forest_ids : object
            A sequence of IDs of forests to which the search should be constrained. An
            empty sequence means search all forests in the database. The default is an
            empty sequence.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:match-regions
        """
        expr = Cts.match_regions(
            range_indexes=range_indexes,
            operation=operation,
            regions=regions,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:max`` via ``/v1/eval``.

        Returns the maximal value given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:max
        """
        expr = Cts.max(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def median(self, arg, **kwargs) -> list:
        """Execute ``cts:median`` via ``/v1/eval``.

        Returns a frequency-weighted median of a sequence.

        Parameters
        ----------
        arg : object
            The sequence of values. The values should be the result of a lexicon lookup.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:median
        """
        expr = Cts.median(arg=arg)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:min`` via ``/v1/eval``.

        Returns the minimal value given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:min
        """
        expr = Cts.min(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def part_of_speech(self, token, **kwargs) -> list:
        """Execute ``cts:part-of-speech`` via ``/v1/eval``.

        Returns the part of speech for a cts:token, if any.

        Parameters
        ----------
        token : object
            A token, as returned from cts:tokenize .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:part-of-speech
        """
        expr = Cts.part_of_speech(token=token)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def percent_rank(self, arg, value, *, options=None, **kwargs) -> list:
        """Execute ``cts:percent-rank`` via ``/v1/eval``.

        Returns the rank of a value in a data set as a percentage of the data
        set.

        Parameters
        ----------
        arg : object
            The sequence of values.
        value : object
            The value to be "ranked".
        options : object
            Options. The default is (). Options include: "ascending"(default) Rank the
            value as if the sequence was sorted in ascending order. "descending" Rank
            the value as if the sequence was sorted in descending order. "collation= URI
            " Applies only when $arg is of the xs:string type. If no specified, the
            default collation is used. "coordinate-system= name " Applies only when $arg
            is of the cts:point type. If no specified, the default coordinate system is
            used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:percent-rank
        """
        expr = Cts.percent_rank(arg=arg, value=value, options=options)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def percentile(self, arg, p, **kwargs) -> list:
        """Execute ``cts:percentile`` via ``/v1/eval``.

        Returns a sequence of percentile(s) given a sequence of percentage(s).

        Parameters
        ----------
        arg : object
            The sequence of values. The values should be the result of a lexicon lookup.
        p : object
            The sequence of percentage(s).
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:percentile
        """
        expr = Cts.percentile(arg=arg, p=p)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def period_compare(self, period_1, operator, period_2, **kwargs) -> list:
        """Execute ``cts:period-compare`` via ``/v1/eval``.

        Compares two periods using the specified comparison operator.

        Parameters
        ----------
        period_1 : object
            The first period to compare.
        operator : object
            A comparison operator.
        period_2 : object
            The second period to compare against the first.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:period-compare
        """
        expr = Cts.period_compare(
            period_1=period_1,
            operator=operator,
            period_2=period_2,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def quality(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:quality`` via ``/v1/eval``.

        Returns the quality of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:quality
        """
        expr = Cts.quality(node=node)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def rank(self, arg, value, *, options=None, **kwargs) -> list:
        """Execute ``cts:rank`` via ``/v1/eval``.

        Returns the rank of a value in a data set.

        Parameters
        ----------
        arg : object
            The sequence of values.
        value : object
            The value to be "ranked".
        options : object
            Options. The default is (). Options include: "ascending"(default) Rank the
            value as if the sequence was sorted in ascending order. "descending" Rank
            the value as if the sequence was sorted in descending order. "collation= URI
            " Applies only when $arg is of the xs:string type. If no specified, the
            default collation is used. "coordinate-system= name " Applies only when $arg
            is of the cts:point type. If no specified, the default coordinate system is
            used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:rank
        """
        expr = Cts.rank(arg=arg, value=value, options=options)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def register(self, query, **kwargs) -> list:
        """Execute ``cts:register`` via ``/v1/eval``.

        Register a query for later use.

        Parameters
        ----------
        query : object
            A query to register.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:register
        """
        expr = Cts.register(query=query)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def relevance_info(
        self,
        *,
        node=None,
        output_kind=None,
        **kwargs,
    ) -> list:
        """Execute ``cts:relevance-info`` via ``/v1/eval``.

        Return the relevance score computation report for a node.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation. If this parameter is omitted, the context node is used.
        output_kind : object
            The output kind. It can be either "element" or "object". With "element", the
            built-in returns an XML element. With "object", the built-in returns a
            map:map. The default is "element".
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:relevance-info
        """
        expr = Cts.relevance_info(node=node, output_kind=output_kind)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def remainder(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:remainder`` via ``/v1/eval``.

        Returns an estimated search result size for a node, or of the context
        node if no node is provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation. If you specify the first item from a cts:search expression, then
            cts:remainder will return an estimate of the number of fragments that match
            that expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:remainder
        """
        expr = Cts.remainder(node=node)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def score(self, *, node=None, **kwargs) -> list:
        """Execute ``cts:score`` via ``/v1/eval``.

        Returns the score of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : object
            A node. Typically this is an item in the result sequence of a cts:search
            operation.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:score
        """
        expr = Cts.score(node=node)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:stddev`` via ``/v1/eval``.

        Returns a frequency-weighted sample standard deviation given a value
        lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:stddev
        """
        expr = Cts.stddev(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:stddev-p`` via ``/v1/eval``.

        Returns a frequency-weighted standard deviation of the population given
        a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:stddev-p
        """
        expr = Cts.stddev_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:stem`` via ``/v1/eval``.

        Returns the stem(s) for a word.

        Parameters
        ----------
        text : object
            A word or phrase to stem.
        language : object
            A language to use for stemming. If not supplied, it uses the database
            default language.
        part_of_speech : object
            A part of speech to use for stemming. The default is the unspecified part of
            speech. This parameter is for testing custom stemmers.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:stem
        """
        expr = Cts.stem(text=text, language=language, part_of_speech=part_of_speech)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:sum-aggregate`` via ``/v1/eval``.

        Returns the sum of the values given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:sum-aggregate
        """
        expr = Cts.sum_aggregate(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:thresholds`` via ``/v1/eval``.

        Compute precision, recall, the F measure, and thresholds for the classes
        computed by the classifier, by comparing with the labels for the same
        set.

        Parameters
        ----------
        computed_labels : object
            A sequence of element nodes containing the labels from classification (the
            output from cts:classify ) for a set of documents.
        known_labels : object
            A sequence of element nodes containing the known labels for the same set of
            documents.
        recall_weight : object
            The factor to use in the calculation of the F measure. The number should be
            non-negative. A value of 0 means F is just precision and a value of +INF
            means F is just recall. The default is 1, which gives the harmonic mean
            between precision and recall.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:thresholds
        """
        expr = Cts.thresholds(
            computed_labels=computed_labels,
            known_labels=known_labels,
            recall_weight=recall_weight,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def tokenize(self, text, *, language=None, field=None, **kwargs) -> list:
        """Execute ``cts:tokenize`` via ``/v1/eval``.

        Tokenizes text into words, punctuation, and spaces.

        Parameters
        ----------
        text : object
            A word or phrase to tokenize.
        language : object
            A language to use for tokenization. If not supplied, it uses the database
            default language.
        field : object
            A field to use for tokenization. If the field has custom tokenization rules,
            they will be used. If no field is supplied or the field has no custom
            tokenization rules, the default tokenization rules are used.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:tokenize
        """
        expr = Cts.tokenize(text=text, language=language, field=field)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:train`` via ``/v1/eval``.

        Produces a set of classifiers from a list of labeled training documents.

        Parameters
        ----------
        training_nodes : object
            The sequence of training nodes. These are nodes that represent members of
            the classes.
        labels : object
            A sequence of labels for the training nodes, in the order corresponding to
            the training nodes.
        options : object
            Options with which to customize this operation. You can specify options as
            either an XML element in the "cts:train" namespace, or as a map:map . The
            options names below are XML element localnames. When using a map, replace
            the hyphens with camel casing. For example, "an-option" becomes "anOption"
            when used as a map:map key. The following is a sample options node :
            <options xmlns="cts:train"> <classifier-type>supports</classifier-type>
            <kernel>geodesic</kernel> </options> This function supports the following
            options: < classifier-type > A string defining the kind of classifier to
            produce, either weights or supports . The default is weights . < kernel > A
            string defining which function to use for comparing documents. The default
            is sqrt . Normalization (the values that end in -normalized ) brings
            document vectors into the unit sphere, which may improve the mathematical
            properties of the calculations. Possible values are: simple Model documents
            as 1 or 0 for presence or absence of each term. simple-normalized Like
            simple , but normalized by the square root of the document length. sqrt
            Model documents using the square root of the term frequencies.
            sqrt-normalized Like sqrt , but normalized by the sum of the term
            frequencies. linear-normalized Model documents as the term frequencies
            normalized by the square root of the sum of the squares of the term
            frequencies. gaussian Compare documents using the Gaussian of the term
            frequencies. Requires a classifier-type of supports . geodesic Compare
            documents using the Riemann geodesic distance over term frequencies.
            Requires a classifier-type of supports . < max-terms > An integer defining
            the maximum number of terms to use to represent each document. If a positive
            number M is given, then the M most discriminating terms are used; other
            terms are dropped. The default is 0 (unlimited), but for larger documents a
            value in 500 to 1000 range will produce much better results. < max-support >
            A double specifying the maximum influence a single training node can have.
            This parameter has a strong influence on performance. The default value of
            1.0 should work well in most cases. Larger values means greater sensitivity
            and may improve accuracy on small datasets, but give longer running times.
            Smaller values mean less sensitivity and better resistance to mis-classified
            documents, and shorter running times. < min-weight > A double specifying the
            minimum weight a term can have and still be considered for inclusion in the
            term vector. This parameter only applies to the term weight form of the
            classifier. Smaller values mean longer term vectors and as a consequence
            longer running times and greater memory consumption during classification,
            but may also improve accuracy. The initial value may be adjusted downwards
            during training if a class would otherwise have no terms in its output
            vector. The default is is 0.01. < tolerance > How close the final solutions
            to the constraint equations must be. Smaller values lead to a greater number
            of iterations and longer running times. Larger values lead to less precise
            classification. The default is 0.01. < epsilon > How close a value must be
            to 0 to be counted as equal to 0. Since double arithmetic is not precise,
            setting this value to exactly 0 will likely lead to non-convergence of the
            algorithm. Smaller values lead to a greater number of iterations and longer
            running times. Larger values lead to less precise classification. The
            initial value may be adjusted downwards during execution if it is too large
            to be useful. In general the higher the dimensionality (larger documents,
            larger limits on the number of terms), the smaller this should be. The
            default is 0.01. < max-iterations > The maximum number of iterations of the
            constraint satisfaction algorithm to run. The algorithm usually converges
            very quickly, so this parameter usually has no effect unless it is set very
            low. The default is 500. <thresholds> A definition of the thresholds to use
            in classification. This is a complex element with one or more <threshold>
            children. You can specify both a default value and per-class values (as
            computed from cts:thresholds ). The default value will apply to any classes
            for which a per-class value is not specified. For example: <options
            xmlns="cts:train"> <thresholds> <threshold>-1.0</threshold> <threshold
            class="Example 1">-2.42</threshold> </thresholds> </options> For the initial
            tuning phase of training your data, leave the value of this parameter at its
            default value which is a very large negative number (-1.0e30). This will
            allow you to accurately compute the threshold values when you run
            cts:thresholds on the initial training data. Then you can use the calculated
            threshold values when you run the secondary pass through the second part of
            your training data. < use-db-config > A boolean value indicating whether to
            use the current DB configuration for determining which terms to use. The
            default is false , which means that only the indexing options in the options
            node will be used for calculating the classifier. The options element also
            includes indexing options in the http://marklogic.com/xdmp/database
            namespace. These control which terms to use. Note that the use of certain
            options, such as fast-case-sensitive-searches , will not impact final
            results unless the term vector size is limited with the max-terms option.
            Other options, such as phrase-throughs , will only generate terms if some
            other option is also enabled (in this case fast-phrase-searches ). The
            database options are the same as the database options shown for
            cts:distinctive-terms .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:train
        """
        expr = Cts.train(training_nodes=training_nodes, labels=labels, options=options)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def triple_value_statistics(
        self,
        *,
        values=None,
        forest_ids=None,
        **kwargs,
    ) -> list:
        """Execute ``cts:triple-value-statistics`` via ``/v1/eval``.

        Returns statistics from the triple index for the values given.

        Parameters
        ----------
        values : object
            The values to look up.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:triple-value-statistics
        """
        expr = Cts.triple_value_statistics(values=values, forest_ids=forest_ids)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:triples`` via ``/v1/eval``.

        Returns values from the triple index.

        Parameters
        ----------
        subject : object
            The subjects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        predicate : object
            The predicates to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        object : object
            The objects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        operator : object
            If a single string is provided it is treated as the operator for the $object
            values. If a sequence of three strings are provided, they give the operators
            for $subject, $predicate and $object in turn. The default operator is "=".
            Operators include: "sameTerm" Match triple index values which are the same
            RDF term as $value. This compares aspects of values that are ignored in XML
            Schema comparison semantics, like timezone and derived type of $value. "<"
            Match range index values less than $value. "<=" Match range index values
            less than or equal to $value. ">" Match range index values greater than
            $value. ">=" Match range index values greater than or equal to $value. "="
            Match range index values equal to $value. "!=" Match range index values not
            equal to $value.
        options : object
            Options. The default is (). Options include: "order-pso" Return results
            ordered by predicate, then subject, then object. "order-sop" Return results
            ordered by subject, then object, then predicate. "order-ops" Return results
            ordered by object, then predicate, then subject. "quads" Return quads that
            include values for the named graph that the triples are in. Requires the
            collection lexicon enabled. "any" Values from any fragment should be
            included. "document" Values from document fragments should be included.
            "properties" Values from properties fragments should be included. "locks"
            Values from locks fragments should be included. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "checked" Word positions should be checked when resolving
            the query. "unchecked" Word positions should not be checked when resolving
            the query. "too-many-positions-error" If too much memory is needed to
            perform positions calculations to check whether a document matches a query,
            return an XDMP-TOOMANYPOSITIONS error, instead of accepting the document as
            a match. "eager" Perform work concurrently whilst returning triples from the
            index - buffering some results into memory. This usually takes the shortest
            time when returning a complete result. "lazy" Perform only some the work
            concurrently before returning the first triple from the index, and most of
            the work sequentially while iterating through the rest of the triples. This
            usually takes the shortest time when returning a partial result.
            "concurrent" Perform the work concurrently in another thread. This is a hint
            to the query optimizer to help parallelize the lexicon work, allowing the
            calling query to continue performing other work while the lexicon processing
            occurs. This is especially useful in cases where multiple lexicon calls
            occur in the same query (for example, resolving many facets in a single
            query).
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:triples
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
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:uri-match`` via ``/v1/eval``.

        Returns values from the URI lexicon that match the specified wildcard
        pattern.

        Parameters
        ----------
        pattern : object
            Wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" URIs should be returned in
            ascending order. "descending" URIs should be returned in descending order.
            "any" URIs from any fragment should be included. "document" URIs from
            document fragments should be included. "properties" URIs from properties
            fragments should be included. "locks" URIs from locks fragments should be
            included. "frequency-order" URIs should be returned ordered by frequency.
            "item-order" URIs should be returned ordered by item. "limit= N " Return no
            more than N URIs. You should not use this option with the "skip" option. Use
            "truncate" instead. "skip= N " Skip over fragments selected by the cts:query
            to treat the Nth fragment as the first fragment. URIs from skipped fragments
            are not included. This option affects the number of fragments selected by
            the cts:query to calculate frequencies. Only applies when a $query parameter
            is specified. "sample= N " Return only URIs from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only URIs from
            the first N fragments after skip selected by the cts:query . This option
            also affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[str]
            A list of URI strings; empty when no URIs match.

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
        Native reference: https://docs.marklogic.com/cts:uri-match
        """
        expr = Cts.uri_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ranged(expr, range, index)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_document_patch_path(
        self,
        string,
        *,
        map=None,
        **kwargs,
    ) -> list:
        """Execute ``cts:valid-document-patch-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-document-patch-path
        """
        expr = Cts.valid_document_patch_path(string=string, map=map)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_extract_path(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-extract-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-extract-path
        """
        expr = Cts.valid_extract_path(string=string, map=map)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_index_path(self, string, ignorens, **kwargs) -> list:
        """Execute ``cts:valid-index-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces based on the server run-
        time environment.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        ignorens : object
            Ignore namespace prefix binding errors.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-index-path
        """
        expr = Cts.valid_index_path(string=string, ignorens=ignorens)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_optic_path(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-optic-path`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-optic-path
        """
        expr = Cts.valid_optic_path(string=string, map=map)
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def valid_tde_context(self, string, *, map=None, **kwargs) -> list:
        """Execute ``cts:valid-tde-context`` via ``/v1/eval``.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : object
            The path to be tested as a string.
        map : object
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:valid-tde-context
        """
        expr = Cts.valid_tde_context(string=string, map=map)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:value-co-occurrences`` via ``/v1/eval``.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified value lexicon(s).

        Parameters
        ----------
        range_index_1 : object
            A reference to a range index.
        range_index_2 : object
            A reference to a range index.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "timezone=
            TZ " Return timezone sensitive values (dateTime, time, date, gYearMonth,
            gYear, gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N co-occurrences. You should not
            use this option with the "skip" option. Use "truncate" instead. "skip= N "
            Skip over fragments selected by the cts:query to treat the Nth fragment as
            the first fragment. Co-occurrences from skipped fragments are not included.
            This option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. Return only co-occurrences from the
            first N fragments after skip selected by the cts:query , bit do not affect
            frequencies. Only applies when a $query parameter is specified. "truncate= N
            " Include only co-occurrences from the first N fragments after skip selected
            by the cts:query . This option also affects the number of fragments selected
            by the cts:query to calculate frequencies. Only applies when a $query
            parameter is specified. "score-logtfidf" Compute scores using the logtfidf
            method. Only applies when a $query parameter is specified. "score-logtf"
            Compute scores using the logtf method. Only applies when a $query parameter
            is specified. "score-simple" Compute scores using the simple method. Only
            applies when a $query parameter is specified. "score-random" Compute scores
            using the random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an
            element(cts:co-occurrence)* sequence .
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:value-co-occurrences
        """
        expr = Cts.value_co_occurrences(
            range_index_1=range_index_1,
            range_index_2=range_index_2,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:value-match`` via ``/v1/eval``.

        Returns values from the specified value lexicon(s) that match the
        specified wildcard pattern.

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        pattern : object
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Values should be returned in
            ascending order. "descending" Values should be returned in descending order.
            "any" Values from any fragment should be included. "document" Values from
            document fragments should be included. "properties" Values from properties
            fragments should be included. "locks" Values from locks fragments should be
            included. "frequency-order" Values should be returned ordered by frequency.
            "item-order" Values should be returned ordered by item. "fragment-frequency"
            Frequency should be the number of fragments with an included value. This
            option is used with cts:frequency . "item-frequency" Frequency should be the
            number of occurrences of an included value. This option is used with
            cts:frequency . "timezone= TZ " Return timezone sensitive values (dateTime,
            time, date, gYearMonth, gYear, gMonth, and gDay) adjusted to the timezone
            specified by TZ . Example timezones: Z, -08:00, +01:00. "limit= N " Return
            no more than N values. You should not use this option with the "skip"
            option. Use "truncate" instead. "skip= N " Skip over fragments selected by
            the cts:query to treat the Nth fragment as the first fragment. Values from
            skipped fragments are not included. This option affects the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "sample= N " Return only values from
            the first N fragments after skip selected by the cts:query . This option
            does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only values from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence .
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:value-match
        """
        expr = Cts.value_match(
            range_indexes=range_indexes,
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:value-ranges`` via ``/v1/eval``.

        Returns value ranges from the specified value lexicon(s).

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        bounds : object
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : object
            Options. The default is (). Options include: "ascending" Ranges should be
            returned in ascending order. "descending" Ranges should be returned in
            descending order. "empties" Include fully-bounded ranges whose frequency is
            0. These ranges will have no minimum or maximum value. Only empty ranges
            that have both their upper and lower bounds specified in the $bounds options
            are returned; any empty ranges that are less than the first bound or greater
            than the last bound are not returned. For example, if you specify 4 bounds
            and there are no results for any of the bounds, 3 elements are returned (not
            5 elements). "any" Values from any fragment should be included. "document"
            Values from document fragments should be included. "properties" Values from
            properties fragments should be included. "locks" Values from locks fragments
            should be included. "frequency-order" Ranges should be returned ordered by
            frequency. "item-order" Ranges should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included value. This option is used with cts:frequency . "item-frequency"
            Frequency should be the number of occurrences of an included value. This
            option is used with cts:frequency . "timezone= TZ " Return timezone
            sensitive values (dateTime, time, date, gYearMonth, gYear, gMonth, and gDay)
            adjusted to the timezone specified by TZ . Example timezones: Z, -08:00,
            +01:00. "limit= N " Return no more than N ranges. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Values from skipped fragments are not included. This option
            affects the number of fragments selected by the cts:query to calculate
            frequencies. Only applies when a $query parameter is specified. "sample= N "
            Return only ranges for buckets with at least one value from the first N
            fragments after skip selected by the cts:query . This option does not affect
            the number of fragments selected by the cts:query to calculate frequencies.
            Only applies when a $query parameter is specified. "truncate= N " Include
            only values from the first N fragments after skip selected by the cts:query
            . This option also affects the number of fragments selected by the cts:query
            to calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
        query : object
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:value-ranges
        """
        expr = Cts.value_ranges(
            range_indexes=range_indexes,
            bounds=bounds,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:value-tuples`` via ``/v1/eval``.

        Returns value co-occurrence tuples (that is, tuples of values, each of
        which appear in the same fragment) from the specified value lexicons.

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        options : object
            Options. The default is (). Options include: "ascending" Co-occurrences
            should be returned in ascending order. "descending" Co-occurrences should be
            returned in descending order. "any" Co-occurrences from any fragment should
            be included. "document" Co-occurrences from document fragments should be
            included. "properties" Co-occurrences from properties fragments should be
            included. "locks" Co-occurrences from locks fragments should be included.
            "frequency-order" Co-occurrences should be returned ordered by frequency.
            "item-order" Co-occurrences should be returned ordered by item.
            "fragment-frequency" Frequency should be the number of fragments with an
            included co-occurrences. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included co-occurrence. This option is used with cts:frequency . "timezone=
            TZ " Return timezone sensitive values (dateTime, time, date, gYearMonth,
            gYear, gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "ordered" Include co-occurrences only when the
            value from the first lexicon appears before the value from the second
            lexicon. Requires that word positions be enabled for both lexicons.
            "proximity= N " Include co-occurrences only when the values appear within N
            words of each other. Requires that word positions be enabled for both
            lexicons. "limit= N " Return no more than N tuples. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Co-occurrences from skipped fragments are not included. This
            option affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "sample= N " Return only co-occurrences from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only
            co-occurrences from the first N fragments after skip selected by the
            cts:query . This option also affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "score-logtfidf" Compute scores using the logtfidf method. Only
            applies when a $query parameter is specified. "score-logtf" Compute scores
            using the logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query).
        query : object
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:value-tuples
        """
        expr = Cts.value_tuples(
            range_indexes=range_indexes,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:variance`` via ``/v1/eval``.

        Returns a frequency-weighted sample variance given a value lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:variance
        """
        expr = Cts.variance(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:variance-p`` via ``/v1/eval``.

        Returns a frequency-weighted variance of the population given a value
        lexicon.

        Parameters
        ----------
        range_index : object
            Reference to a range index. The type of the range index must be numeric.
        options : object
            Same as the "options" parameter in cts:aggregate .
        query : object
            Same as the "query" parameter in cts:aggregate .
        forest_ids : object
            Same as the "forest-ids" parameter in cts:aggregate .
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:variance-p
        """
        expr = Cts.variance_p(
            range_index=range_index,
            options=options,
            query=query,
            forest_ids=forest_ids,
        )
        return await self._execute_native(
            expr,
            **_execution_options(self._namespaces, kwargs),
        )

    async def walk(self, node, query, expr, **kwargs) -> list:
        """Execute ``cts:walk`` via ``/v1/eval``.

        Walks a node, evaluating an expression with any text matching a query.

        Parameters
        ----------
        node : object
            A node to walk. The node must be either a document node or an element node;
            it cannot be a text node.
        query : object
            A query specifying the text on which to evaluate the expression. If a string
            is entered, the string is treated as a cts:word-query of the specified
            string.
        expr : object
            An expression to evaluate with matching text. You can use the variables
            $cts:text , $cts:node , $cts:queries , $cts:start , and $cts:action
            (described below) in the expression.
        kwargs : dict
            Execution keywords: database, txid, output_type, timeout and namespaces.

        Returns
        -------
        list
            A list of native parsed results, including for a single result.

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
        Native reference: https://docs.marklogic.com/cts:walk
        """
        expr = Cts.walk(node=node, query=query, expr=expr)
        return await self._execute_native(
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
    ) -> list:
        """Execute ``cts:word-match`` via ``/v1/eval``.

        Returns words from the word lexicon that match the wildcard pattern.

        Parameters
        ----------
        pattern : object
            A wildcard pattern to match.
        options : object
            Options. The default is (). Options include: "case-sensitive" A
            case-sensitive match. "case-insensitive" A case-insensitive match.
            "diacritic-sensitive" A diacritic-sensitive match. "diacritic-insensitive" A
            diacritic-insensitive match. "ascending" Words should be returned in
            ascending order. "descending" Words should be returned in descending order.
            "any" Words from any fragment should be included. "document" Words from
            document fragments should be included. "properties" Words from properties
            fragments should be included. "locks" Words from locks fragments should be
            included. "collation= URI " Use the lexicon with the collation specified by
            URI . "limit= N " Return no more than N words. You should not use this
            option with the "skip" option. Use "truncate" instead. "skip= N " Skip over
            fragments selected by the cts:query to treat the Nth fragment as the first
            fragment. Words from skipped fragments are not included. Only applies when a
            $query parameter is specified. "sample= N " Return only words from the first
            N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "truncate= N " Include only words from the
            first N fragments after skip selected by the cts:query . Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "concurrent" Perform the work
            concurrently in another thread. This is a hint to the query optimizer to
            help parallelize the lexicon work, allowing the calling query to continue
            performing other work while the lexicon processing occurs. This is
            especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:word-match
        """
        expr = Cts.word_match(
            pattern=pattern,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
    ) -> list:
        """Execute ``cts:words`` via ``/v1/eval``.

        Returns words from the word lexicon.

        Parameters
        ----------
        start : object
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : object
            Options. The default is (). Options include: "ascending" Words should be
            returned in ascending order. "descending" Words should be returned in
            descending order. "any" Words from any fragment should be included.
            "document" Words from document fragments should be included. "properties"
            Words from properties fragments should be included. "locks" Words from locks
            fragments should be included. "collation= URI " Use the lexicon with the
            collation specified by URI . "limit= N " Return no more than N words. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Words from skipped fragments are not
            included. Only applies when a $query parameter is specified. "sample= N "
            Return only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified. "truncate= N
            " Include only words from the first N fragments after skip selected by the
            cts:query . Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "concurrent" Perform the work concurrently in another
            thread. This is a hint to the query optimizer to help parallelize the
            lexicon work, allowing the calling query to continue performing other work
            while the lexicon processing occurs. This is especially useful in cases
            where multiple lexicon calls occur in the same query (for example, resolving
            many facets in a single query). "map" Return results as a single map:map
            value instead of as an xs:string* sequence .
        query : object
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : object
            Inclusive server-side selection; N means [1, N].
        index : object
            One-based position; cannot be combined with range.
        kwargs : dict
            Execution keywords: database, txid, timeout and namespaces.

        Returns
        -------
        list[ValueHit]
            A list of parsed values with frequencies; empty when no values match.

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
        Native reference: https://docs.marklogic.com/cts:words
        """
        expr = Cts.words(
            start=start,
            options=options,
            query=query,
            quality_weight=quality_weight,
            forest_ids=forest_ids,
        )
        expr = _ResultPairs(_ranged(expr, range, index), ValueHit, options=options)
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
        self._rest = rest

    async def _execute_native(
        self,
        expr,
        *,
        namespaces=None,
        database=None,
        txid=None,
        output_type=None,
        timeout=UNSET,
    ) -> list:
        """Execute a native expression and retain its result sequence.

        Parameters
        ----------
        expr : XqyExpression
            CTS operation to execute without score/frequency pairing.
        namespaces : dict | None
            Namespace declarations for compilation.
        database : str | None
            Target content database.
        txid : str | None
            Existing transaction identifier.
        output_type : type | None
            Per-item str/bytes conversion, or None for parsed values.
        timeout : object
            HTTP timeout override; UNSET inherits client configuration.

        Returns
        -------
        list
            One entry per response part; JSON arrays remain nested lists.

        Raises
        ------
        ValueError
            If output_type is not None, str or bytes.
        MarkLogicError
            If the server rejects the evaluation.
        HTTPStatusError
            If another HTTP failure occurs.
        """
        if output_type not in (None, str, bytes):
            message = "output_type must be None, str or bytes"
            raise ValueError(message)
        code, variables = expr.compile(namespaces=namespaces)
        response = await self._rest.eval.post(
            xquery=code,
            variables=variables,
            database=database,
            txid=txid,
            timeout=timeout,
        )
        MLResponseParser.raise_for_status(response)
        if not response.content:
            return []
        parts = MLResponseParser.parse_with_headers(response, output_type)
        if isinstance(parts, tuple):
            parts = [parts]
        return [content for _, content in parts]

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
        list[SearchHit] | list[ValueHit]
            A list of result objects, including for a single result.

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
    ) -> list:
        """Execute ``cts:search`` via ``/v1/eval``.

        Returns a relevance-ordered sequence of nodes specified by a given
        query.

        Parameters
        ----------
        expression : str | XqyExpression | None
            An expression to be searched. This must be an inline fully searchable path
            expression. Python strings are wrapped internally and validated
            with the other literal paths in the expression before execution.
        query : XqyExpression | None
            A cts:query specifying the search to perform. If a string is entered, the
            string is treated as a cts:word-query of the specified string.
        options : object
            Options to this search. The default is (). Options include: "filtered" A
            filtered search (the default). Filtered searches eliminate any
            false-positive matches and properly resolve cases where there are multiple
            candidate matches within the same fragment. Filtered search results fully
            satisfy the specified cts:query . "unfiltered" An unfiltered search. An
            unfiltered search selects fragments from the indexes that are candidates to
            satisfy the specified cts:query , and then it returns a single node from
            within each fragment that satisfies the specified searchable path
            expression. Unfiltered searches are useful because of the performance they
            afford when jumping deep into the result set (for example, when paginating a
            long result set and jumping to the 1,000,000th result). However, depending
            on the searchable path expression, the cts:query specified, the structure of
            the documents in the database, and the configuration of the database,
            unfiltered searches may yield false-positive results being included in the
            search results. Unfiltered searches may also result in missed matches or in
            incorrect matches, especially when there are multiple candidate matches
            within a single fragment. To avoid these problems, you should only use
            unfiltered searches on top-level XPath expressions (for example, document
            nodes, collections, directories) or on fragment roots. Using unfiltered
            searches on complex XPath expressions or on XPath expressions that traverse
            below a fragment root can result in unexpected results. "score-logtfidf"
            Compute scores using the logtfidf method (the default scoring method). This
            uses the formula: log(term frequency) * (inverse document frequency)
            "score-logtf" Compute scores using the logtf method. This does not take into
            account how many documents have the term and uses the formula: log(term
            frequency) "score-simple" Compute scores using the simple method. The
            score-simple method gives a score of 8*weight for each matching term in the
            cts:query expression, and then scales the score up by multiplying by 256. It
            does not matter how many times a given term matches (that is, the term
            frequency does not matter); each match contributes 8*weight to the score.
            For example, the following query (assume the default weight of 1) would give
            a score of 8*256=2048 for any fragment with one or more matches for "hello",
            a score of 16*256=4096 for any fragment that also has one or more matches
            for "goodbye", or a score of zero for fragments that have no matches for
            either term: cts:or-query(("hello", "goodbye")) "score-random" Compute
            scores using the random method. The score-random method gives a random value
            to the score. You can use this to randomly choose fragments matching a
            query. "score-zero" Compute all scores as zero. When combined with a quality
            weight of zero, this is the fastest consistent scoring method. "score-bm25"
            Compute scores using the bm25 method. This uses the formula: (log(term
            frequency) / (1-'bm25-length-weight'+'bm25-length-weight'*(doc length /
            average doc length))) * (inverse document frequency) "checked" Word
            positions are checked (the default) when resolving the query. Checked
            searches eliminate false-positive matches for phrases during the index
            resolution phase of search processing. "unchecked" Word positions are not
            checked when resolving the query. Unchecked searches do not take into
            account word positions and can lead to false-positive matches during the
            index resolution phase of search processing. This setting is useful for
            debugging, but not recommended for normal use. "too-many-positions-error" If
            too much memory is needed to perform positions calculations to check whether
            a document matches a query, return an XDMP-TOOMANYPOSITIONS error, instead
            of accepting the document as a match. "faceted" Do a little more work to
            save faceting information about fragments matching this search so that
            calculating facets will be faster. "unfaceted" Do not save faceting
            information about fragments matching this search. "relevance-trace" Collect
            relevance score computation details with which you can generate a trace
            report using cts:relevance-info . Collecting this information is costly and
            will significantly slow down your search, so you should only use it when
            using cts:relevance-info to tune a query. "format- FORMAT " Limit the search
            to documents in document format specified by FORMAT (binary, json, text, or
            xml) cts:order Specification A sequence of cts:order specifications. The
            order is evaluated in the order each appears in the sequence. Default:
            (cts:score-order("descending"),cts:document-order("ascending")) . The
            sequence typically consists of one or more of: cts:index-order ,
            cts:score-order , cts:confidence-order , cts:fitness-order ,
            cts:quality-order , cts:document-order , cts:unordered . When using
            cts:index-order , there must be a range index defined on the index(es)
            specified by the cts:reference specification (for example,
            cts:element-reference .) "bm25-length-weight= NUMBER " The weight of the
            document length to average document length ratio while using the
            "score-BM25" option. Valid values are greater than 0.0 and less than or
            equal to 1.0. The default is 0.333.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            (). In the XQuery version, you can use cts:search with this parameter and an
            empty cts:and-query to specify a forest-specific XPath statement (see the
            third example below). If you use this to constrain an XPath to one or more
            forests, you should set the quality-weight to zero to keep the XPath
            document order.
        range : Range | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns [item] or [].
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
        list
            Always a list; empty sequences return [] and singletons return [item].

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:search
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
    ) -> list:
        """Execute ``cts:uris`` via ``/v1/eval``.

        Returns values from the URI lexicon.

        Parameters
        ----------
        start : object
            A starting value. Return only this value and following values. If the empty
            string, return all values. If the parameter is not in the lexicon, then it
            returns the values beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" URIs should be
            returned in ascending order. "descending" URIs should be returned in
            descending order. "any" URIs from any fragment should be included.
            "document" URIs from document fragments should be included. "properties"
            URIs from properties fragments should be included. "locks" URIs from locks
            fragments should be included. "frequency-order" URIs should be returned
            ordered by frequency. "item-order" URIs should be returned ordered by item.
            "limit= N " Return no more than N URIs. You should not use this option with
            the "skip" option. Use "truncate" instead. "skip= N " Skip over fragments
            selected by the cts:query to treat the Nth fragment as the first fragment.
            URIs from skipped fragments are not included. This option affects the number
            of fragments selected by the cts:query to calculate frequencies. Only
            applies when a $query parameter is specified. "sample= N " Return only URIs
            from the first N fragments after skip selected by the cts:query . This
            option does not affect the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "truncate= N " Include only URIs from the first N fragments after skip
            selected by the cts:query . This option also affects the number of fragments
            selected by the cts:query to calculate frequencies. Only applies when a
            $query parameter is specified. "score-logtfidf" Compute scores using the
            logtfidf method. Only applies when a $query parameter is specified.
            "score-logtf" Compute scores using the logtf method. Only applies when a
            $query parameter is specified. "score-simple" Compute scores using the
            simple method. Only applies when a $query parameter is specified.
            "score-random" Compute scores using the random method. Only applies when a
            $query parameter is specified. "score-zero" Compute all scores as zero. Only
            applies when a $query parameter is specified. "checked" Word positions
            should be checked when resolving the query. "unchecked" Word positions
            should not be checked when resolving the query. "too-many-positions-error"
            If too much memory is needed to perform positions calculations to check
            whether a document matches a query, return an XDMP-TOOMANYPOSITIONS error,
            instead of accepting the document as a match. "eager" Perform most of the
            work concurrently before returning the first item from the indexes, and only
            some of the work sequentially while iterating through the rest of the items.
            This usually takes the shortest time for a complete item-order result or for
            any frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:string* sequence .
        query : XqyExpression | None
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : Range | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns [item] or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        list[str]
            Always a list; empty sequences return [] and singletons return [item].

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:uris
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
        return await self._execute_native(
            expr,
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
    ) -> list:
        """Execute ``cts:values`` via ``/v1/eval``.

        Returns values from the specified value lexicon(s).

        Parameters
        ----------
        range_indexes : object
            A sequence of references to range indexes.
        start : object
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : object
            Options. The default is (). Options include: "ascending" Values should be
            returned in ascending order. "descending" Values should be returned in
            descending order. "any" Values from any fragment should be included.
            "document" Values from document fragments should be included. "properties"
            Values from properties fragments should be included. "locks" Values from
            locks fragments should be included. "frequency-order" Values should be
            returned ordered by frequency. "item-order" Values should be returned
            ordered by item. "fragment-frequency" Frequency should be the number of
            fragments with an included value. This option is used with cts:frequency .
            "item-frequency" Frequency should be the number of occurrences of an
            included value. This option is used with cts:frequency . "timezone= TZ "
            Return timezone sensitive values (dateTime, time, date, gYearMonth, gYear,
            gMonth, and gDay) adjusted to the timezone specified by TZ . Example
            timezones: Z, -08:00, +01:00. "limit= N " Return no more than N values. You
            should not use this option with the "skip" option. Use "truncate" instead.
            "skip= N " Skip over fragments selected by the cts:query to treat the Nth
            fragment as the first fragment. Values from skipped fragments are not
            included. This option affects the number of fragments selected by the
            cts:query to calculate frequencies. Only applies when a $query parameter is
            specified. "sample= N " Return only values from the first N fragments after
            skip selected by the cts:query . This option does not affect the number of
            fragments selected by the cts:query to calculate frequencies. Only applies
            when a $query parameter is specified. "truncate= N " Include only values
            from the first N fragments after skip selected by the cts:query . This
            option also affects the number of fragments selected by the cts:query to
            calculate frequencies. Only applies when a $query parameter is specified.
            "score-logtfidf" Compute scores using the logtfidf method. Only applies when
            a $query parameter is specified. "score-logtf" Compute scores using the
            logtf method. Only applies when a $query parameter is specified.
            "score-simple" Compute scores using the simple method. Only applies when a
            $query parameter is specified. "score-random" Compute scores using the
            random method. Only applies when a $query parameter is specified.
            "score-zero" Compute all scores as zero. Only applies when a $query
            parameter is specified. "checked" Word positions should be checked when
            resolving the query. "unchecked" Word positions should not be checked when
            resolving the query. "too-many-positions-error" If too much memory is needed
            to perform positions calculations to check whether a document matches a
            query, return an XDMP-TOOMANYPOSITIONS error, instead of accepting the
            document as a match. "eager" Perform most of the work concurrently before
            returning the first item from the indexes, and only some of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a complete item-order result or for any
            frequency-order result. "lazy" Perform only some the work concurrently
            before returning the first item from the indexes, and most of the work
            sequentially while iterating through the rest of the items. This usually
            takes the shortest time for a small item-order partial result. "concurrent"
            Perform the work concurrently in another thread. This is a hint to the query
            optimizer to help parallelize the lexicon work, allowing the calling query
            to continue performing other work while the lexicon processing occurs. This
            is especially useful in cases where multiple lexicon calls occur in the same
            query (for example, resolving many facets in a single query). "map" Return
            results as a single map:map value instead of as an xs:anyAtomicType*
            sequence .
        query : XqyExpression | None
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().
        range : Range | None
            Inclusive [start, end]; bounds accept positive integers or fn.last().
            N means [1, N]. Cannot be combined with index.
        index : int | XqyExpression | None
            One-based positive position or fn.last(). Returns [item] or [].
        kwargs : dict
            Execution options: database, txid, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        list
            Always a list; empty sequences return [] and singletons return [item].

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        ValueError
            For invalid positions or simultaneous index and range.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:values
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
            _ResultPairs(expr, ValueHit, options=options),
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
    ) -> list:
        """Execute ``cts:estimate`` via ``/v1/eval``.

        Returns the number of fragments selected by a search.

        Parameters
        ----------
        query : XqyExpression | None
            Query to estimate. None supplies the required empty query slot.
        options : object
            Options to this search. The default is (). See cts.search for details on
            available options.
        quality_weight : object
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : object
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            (). In the XQuery version, you can use cts:search with this parameter and an
            empty cts:and-query to specify a forest-specific XPath statement (see the
            third example below). If you use this to constrain an XPath to one or more
            forests, you should set the quality-weight to zero to keep the XPath
            document order.
        maximum : object
            The maximum value to return. Stop selecting fragments if this number is
            reached.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        list
            One aggregate result, optionally converted with output_type.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:estimate
        """
        return await self._execute_native(
            Cts.estimate(
                query,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
                maximum=maximum,
            ),
            **_execution_options(self._namespaces, kwargs),
        )
