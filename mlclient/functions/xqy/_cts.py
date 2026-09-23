# Native signatures retain their parameter names and argument counts.
"""Builders for supported MarkLogic ``cts:`` functions.

The namespace mirrors query constructors, supporting value constructors and
operations that execute searches, lexicon lookups, analytics or text processing.
Accessors that decompose opaque CTS values and deprecated functions are omitted.
Every method is pure and returns an :class:`Expr` for later composition or eval.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import (
    Expr,
    _FunctionCall,
    as_expr,
    index_path,
    namespace_map,
    search_path,
    xpath,
)
from mlclient.functions.xqy._xs import Xs

xs = Xs()

_RANGE_OPERATORS = frozenset({"<", "<=", ">", ">=", "=", "!="})
_DIRECTORY_DEPTHS = frozenset({"1", "infinity"})


def _double(value) -> Expr | None:
    """Cast an optional numeric value to the native double type."""
    return xs.double(value) if value is not None else None


def _qname(value) -> Expr:
    """Convert local-name strings, QName expressions or their sequences."""
    if isinstance(value, (list, tuple)):
        return as_expr(tuple(_qname(item) for item in value))
    return value if isinstance(value, Expr) else xs.qname(value)


def _operator(value, *, required: bool = True) -> Expr | None:
    """Validate a range comparison operator, preserving expression composition.

    Parameters
    ----------
    value : str | Expr | None
        Literal comparison operator or an expression evaluated by MarkLogic.
    required : bool, default True
        Whether None is invalid. False preserves None as an omitted argument.

    Returns
    -------
    Expr | None
        Validated operator expression, or None for an omitted optional operator.

    Raises
    ------
    ValueError
        For an unsupported literal or a missing required operator.
    """
    if value is None and not required:
        return None
    if isinstance(value, Expr):
        return value
    if value not in _RANGE_OPERATORS:
        message = f"unsupported range operator: {value!r}"
        raise ValueError(message)
    return as_expr(value, cast="xs:string")


def _depth(value) -> Expr:
    """Validate a literal directory depth; expressions stay composable."""
    if isinstance(value, Expr):
        return value
    if value not in _DIRECTORY_DEPTHS:
        message = f"directory depth must be '1' or 'infinity': {value!r}"
        raise ValueError(message)
    return as_expr(value, cast="xs:string")


@experimental()
class Cts:
    """Pure builders for supported non-deprecated ``cts:`` functions."""

    @staticmethod
    def after_query(timestamp) -> Expr:
        """Build a composable ``cts:after-query`` call.

        Returns a query matching fragments committed after a specified
        timestamp.

        Parameters
        ----------
        timestamp : xs:unsignedLong
            A commit timestamp. Database fragments committed after this timestamp are
            matched.

        Returns
        -------
        Expr
            Composable call to ``cts:after-query``.

        Notes
        -----
        Fragment commit timestamps change not only by application transactions, but also
        by system transactions from the reindexer or the rebalancer. The query will also
        match fragments whose timestamps have been changed because of reindexing and
        rebalancing after the given timestamp.

        Native reference: https://docs.marklogic.com/cts:after-query
        """
        return _FunctionCall(
            "cts:after-query",
            (timestamp,),
        )

    @staticmethod
    def aggregate(
        native_plugin,
        aggregate_name,
        range_indexes,
        *,
        argument=None,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:aggregate`` call.

        Executes a user-defined extension aggregate function against a value
        lexicon or n-way co-occurrence of multiple value lexicons.

        Parameters
        ----------
        native_plugin : xs:string
            The path to the native plugin library containing the implementation of the
            user-defined extension aggregate.
        aggregate_name : xs:string
            The name of an aggregate function in $native-plugin .
        range_indexes : cts:reference*
            A sequence of references to range indexes. The first range index specified
            in this or any other aggregate function cannot be of type "nullable".
        argument : item()*
            A sequence containing the arguments for the aggregate function. A map can be
            used to pass in multiple sequences of arguments.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:aggregate``.

        Notes
        -----
        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        For details, see Using Aggregate User-Defined Functions in the Search
        Developer's Guide .

        Native reference: https://docs.marklogic.com/cts:aggregate
        """
        return _FunctionCall(
            "cts:aggregate",
            (native_plugin, aggregate_name, range_indexes),
            (argument, options, query, forest_ids),
        )

    @staticmethod
    def and_not_query(positive_query, negative_query) -> Expr:
        """Build a composable ``cts:and-not-query`` call.

        Returns a query specifying the set difference of the matches specified
        by two sub-queries.

        Parameters
        ----------
        positive_query : cts:query
            A positive query, specifying the search results filtered in.
        negative_query : cts:query
            A negative query, specifying the search results to filter out.

        Returns
        -------
        Expr
            Composable call to ``cts:and-not-query``.

        Notes
        -----
        cts:and-not-query

        cts:search

        $negative-query

        cts:and-not-query

        Native reference: https://docs.marklogic.com/cts:and-not-query
        """
        return _FunctionCall(
            "cts:and-not-query",
            (positive_query, negative_query),
        )

    @staticmethod
    def and_query(queries, *, options=None) -> Expr:
        """Build a composable ``cts:and-query`` call.

        Returns a query specifying the intersection of the matches specified by
        the sub-queries.

        Parameters
        ----------
        queries : cts:query*
            A sequence of sub-queries.
        options : xs:string*
            Options to this query. The default is (). Options include: "ordered" An
            ordered and-query, which specifies that the sub-query matches must occur in
            the order of the specified sub-queries. For example, if the sub-queries are
            "cat" and "dog", an ordered query will only match fragments where both "cat"
            and "dog" occur, and where "cat" comes before "dog" in the fragment.
            "unordered" An unordered and-query, which specifies that the sub-query
            matches can occur in any order.

        Returns
        -------
        Expr
            Composable call to ``cts:and-query``.

        Notes
        -----
        If the options parameter contains neither "ordered" nor "unordered", then the
        default is "unordered".

        If you specify the empty sequence for the queries parameter to cts:and-query ,
        you will get a match for every document in the database. For example, the
        following query always returns true:

        cts:contains(collection(), cts:and-query(()))

        In order to match a cts:and-query , the matches from each of the specified
        sub-queries must all occur in the same fragment.

        Native reference: https://docs.marklogic.com/cts:and-query
        """
        return _FunctionCall(
            "cts:and-query",
            (queries,),
            (options,),
        )

    @staticmethod
    def avg_aggregate(
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:avg-aggregate`` call.

        Returns the average of the values given a value lexicon.

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

        Returns
        -------
        Expr
            Composable call to ``cts:avg-aggregate``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:avg-aggregate
        """
        return _FunctionCall(
            "cts:avg-aggregate",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def before_query(timestamp) -> Expr:
        """Build a composable ``cts:before-query`` call.

        Returns a query matching fragments committed before or at a specified
        timestamp.

        Parameters
        ----------
        timestamp : xs:unsignedLong
            A commit timestamp. Database fragments committed before this timestamp are
            matched.

        Returns
        -------
        Expr
            Composable call to ``cts:before-query``.

        Notes
        -----
        Fragment commit timestamps change not only by application transactions, but also
        by system transactions from the reindexer or the rebalancer. The query will also
        match fragments whose timestamps have been changed because of reindexing and
        rebalancing before the given timestamp.

        Native reference: https://docs.marklogic.com/cts:before-query
        """
        return _FunctionCall(
            "cts:before-query",
            (timestamp,),
        )

    @staticmethod
    def boost_query(matching_query, boosting_query) -> Expr:
        """Build a composable ``cts:boost-query`` call.

        Returns a query specifying that matches to $matching-query should have
        their search relevance scores boosted if they also match $boosting-
        query.

        Parameters
        ----------
        matching_query : cts:query
            A sub-query that is used for match and scoring.
        boosting_query : cts:query
            A sub-query that is used only for boosting score.

        Returns
        -------
        Expr
            Composable call to ``cts:boost-query``.

        Notes
        -----
        When used in a search, $boosting-query is not evaluated if there are no matches
        to $matching-query .

        When used in a search, all matches to $matching-query are included in the search
        results. $boosting-query only contributes to search relevances scores. Scoring
        is done the same way as for a cts:and-query .

        Native reference: https://docs.marklogic.com/cts:boost-query
        """
        return _FunctionCall(
            "cts:boost-query",
            (matching_query, boosting_query),
        )

    @staticmethod
    def box(south, west, north, east) -> Expr:
        """Build a composable ``cts:box`` call.

        Returns a geospatial box value.

        Parameters
        ----------
        south : xs:float
            The southern boundary of the box.
        west : xs:float
            The western boundary of the box.
        north : xs:float
            The northern boundary of the box.
        east : xs:float
            The eastern boundary of the box.

        Returns
        -------
        Expr
            Composable call to ``cts:box``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:box
        """
        return _FunctionCall(
            "cts:box",
            (
                as_expr(south, cast="xs:float"),
                as_expr(west, cast="xs:float"),
                as_expr(north, cast="xs:float"),
                as_expr(east, cast="xs:float"),
            ),
        )

    @staticmethod
    def circle(radius, center) -> Expr:
        """Build a composable ``cts:circle`` call.

        Returns a geospatial circle value.

        Parameters
        ----------
        radius : xs:double
            The radius of the circle. The units for the radius is determined at runtime
            by the query options (miles is currently the only option).
        center : cts:point
            A point representing the center of the circle.

        Returns
        -------
        Expr
            Composable call to ``cts:circle``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:circle
        """
        return _FunctionCall(
            "cts:circle",
            (_double(radius), center),
        )

    @staticmethod
    def classify(data_nodes, classifier, *, options=None, training_nodes=None) -> Expr:
        """Build a composable ``cts:classify`` call.

        Classifies a sequence of nodes based on training data.

        Parameters
        ----------
        data_nodes : node()*
            The sequence of nodes to be classified.
        classifier : element(cts:classifier)
            An element node containing the classifier specification. This is typically
            the output of cts:train , either run directly or saved in an XML document in
            the database.
        options : (element()|map:map)?
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
        training_nodes : node()*
            The sequence of training nodes used to train the classifier. Required if the
            supports form of the classifier is used; ignored if the weights form of the
            classifier is used.

        Returns
        -------
        Expr
            Composable call to ``cts:classify``.

        Notes
        -----
        cts:classify classifies a sequence of nodes using the output from cts:train .
        The $data-nodes and $classifier parameters are respectively the nodes to be
        classified and the specification output from cts:train . cts:classify can use
        either supports or weights forms of the $classifier output from cts:train (see
        Output Formats ). If the supports form is used, the training nodes must be
        passed as the 4th parameter. The $options parameter is an options element in the
        cts:classify namespace.

        The output is a sequence of label elements of the form:

        <cts:label> <cts:class name="Example 1" val="-0.003"/> <cts:class name="Example
        2" val="1.4556"/> ... </cts:label>

        { "classes":[ { "name":"animal class", "val":-1 }, { "name":"fruit class",
        "val":-0.875 }, { "name":"vegetable class", "val":-1 } ] },

        Each label corresponds to the data node in the corresponding position in the
        input sequence. There will be a <class> child for each class where the document
        passed the class threshold. The val attribute gives the class membership value
        for the data node in the given class. Values greater than zero indicate likely
        class membership, values less than zero indicate likely non-membership.
        Adjusting thresholds can give more or less selective classification. Increasing
        the threshold leads to a more selective classification (that is, decreases the
        likelihood of classification in the class). Decreasing the threshold gives less
        selective classification.

        Native reference: https://docs.marklogic.com/cts:classify
        """
        return _FunctionCall(
            "cts:classify",
            (data_nodes, classifier),
            (options, training_nodes),
        )

    @staticmethod
    def cluster(nodes, *, options=None) -> Expr:
        """Build a composable ``cts:cluster`` call.

        Produces a set of clusters from a sequence of nodes.

        Parameters
        ----------
        nodes : node()*
            The sequence of nodes to cluster.
        options : (element()|map:map)?
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

        Returns
        -------
        Expr
            Composable call to ``cts:cluster``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:cluster
        """
        return _FunctionCall(
            "cts:cluster",
            (nodes,),
            (options,),
        )

    @staticmethod
    def collection_match(
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:collection-match`` call.

        Returns values from the collection lexicon that match the specified
        wildcard pattern.

        Parameters
        ----------
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:collection-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "sample= N " is not specified in the options parameter, then all included
        URIs may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then URIs from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Native reference: https://docs.marklogic.com/cts:collection-match
        """
        return _FunctionCall(
            "cts:collection-match",
            (pattern,),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def collection_query(uris) -> Expr:
        """Build a composable ``cts:collection-query`` call.

        Match documents in at least one of the specified collections.

        Parameters
        ----------
        uris : xs:string*
            One or more collection URIs. A document matches the query if it is in at
            least one of these collections.

        Returns
        -------
        Expr
            Composable call to ``cts:collection-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:collection-query
        """
        return _FunctionCall(
            "cts:collection-query",
            (uris,),
        )

    @staticmethod
    def collection_reference(*, options=None) -> Expr:
        """Build a composable ``cts:collection-reference`` call.

        Creates a reference to the collection lexicon, for use as a parameter to
        cts:value-tuples.

        Parameters
        ----------
        options : xs:string*
            Options. The default is (). Options include: "nullable" Allow null values in
            tuples reported from cts:value-tuples when using this lexicon. "unchecked"
            Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:collection-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:collection-reference
        """
        return _FunctionCall(
            "cts:collection-reference",
            (),
            (options,),
        )

    @staticmethod
    def collections(
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:collections`` call.

        Returns values from the collection lexicon.

        Parameters
        ----------
        start : xs:string?
            A starting value. Return only this value and following values. If the
            parameter is not in the lexicon, then it returns the values beginning with
            the next value.
        options : xs:string*
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
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:collections``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:collections
        """
        return _FunctionCall(
            "cts:collections",
            (),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def column_range_query(
        schema,
        view,
        column,
        value,
        *,
        operator=None,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:column-range-query`` call.

        Returns a cts:query matching documents matching a TDE-view column equals
        to an value.

        Parameters
        ----------
        schema : xs:string
            The TDE schema name.
        view : xs:string
            The TDE view name.
        column : xs:string
            The TDE column name.
        value : xs:anyAtomicType*
            One or more values used for querying.
        operator : xs:string?
            Operator for the $value values. The default operator is "=". Operators
            include: "<" Match range index values less than $value. "<=" Match range
            index values less than or equal to $value. ">" Match range index values
            greater than $value. ">=" Match range index values greater than or equal to
            $value. "=" Match range index values equal to $value. "!=" Match range index
            values not equal to $value.
        options : xs:string*
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "score-function= function " Use the
            selected scoring function. The score function may be: linear Use a linear
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:column-range-query``.

        Notes
        -----
        This function returns a cts:triple-range-query, and all functions which takes
        cts:triple-range-query as an input can be used (e.g.
        cts:triple-range-query-subject).

        This type of query may only be used in unfiltered search, i.e. cts:search with
        'unfiltered' option, and index lookup, e.g. cts.uris .

        The column parameter must be an indexed column, i.e. does not have the
        virtual=true or belong to a view with viewVirtual=true

        Native reference: https://docs.marklogic.com/cts:column-range-query
        """
        return _FunctionCall(
            "cts:column-range-query",
            (schema, view, column, value),
            (
                _operator(operator, required=False),
                options,
                _double(weight),
            ),
        )

    @staticmethod
    def complex_polygon(outer, inner) -> Expr:
        """Build a composable ``cts:complex-polygon`` call.

        Returns a geospatial complex polygon value.

        Parameters
        ----------
        outer : cts:polygon
            The outer polygon.
        inner : cts:polygon*
            The inner (hole) polygons.

        Returns
        -------
        Expr
            Composable call to ``cts:complex-polygon``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:complex-polygon
        """
        return _FunctionCall(
            "cts:complex-polygon",
            (outer, inner),
        )

    @staticmethod
    def confidence(*, node=None) -> Expr:
        """Build a composable ``cts:confidence`` call.

        Returns the confidence of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : node()
            A node. Typically this is an item in the result sequence of a cts:search
            operation.

        Returns
        -------
        Expr
            Composable call to ``cts:confidence``.

        Notes
        -----
        Confidence is similar to score, except that it is bounded. It is similar to
        fitness, except that it is influenced by term IDFs. It is an xs:float in the
        range of 0.0 to 1.0. It does not include quality.

        When using with any of the scoring methods, the confidence is calculated by
        first bounding the score in the range of 0.0 to 1.0, then taking the square root
        of that number.

        Native reference: https://docs.marklogic.com/cts:confidence
        """
        return _FunctionCall(
            "cts:confidence",
            (),
            (node,),
        )

    @staticmethod
    def confidence_order(*, options=None) -> Expr:
        """Build a composable ``cts:confidence-order`` call.

        Creates a confidence-based ordering clause, for use as an option to
        cts:search.

        Parameters
        ----------
        options : xs:string*
            Options. Options include: "descending" Results should be returned in
            descending order of confidence. "ascending" Results should be returned in
            ascending order of confidence.

        Returns
        -------
        Expr
            Composable call to ``cts:confidence-order``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Native reference: https://docs.marklogic.com/cts:confidence-order
        """
        return _FunctionCall(
            "cts:confidence-order",
            (),
            (options,),
        )

    @staticmethod
    def contains(nodes, query) -> Expr:
        """Build a composable ``cts:contains`` call.

        Returns true if any of a sequence of values matches a query.

        Parameters
        ----------
        nodes : item()*
            The nodes or atomic values to be checked for a match. Atomic values are
            converted to a text node before checking for a match, which may result in an
            error if the value cannot be converted.
        query : cts:query
            A query to match against. If a string is entered, the string is treated as a
            cts:word-query of the specified string.

        Returns
        -------
        Expr
            Composable call to ``cts:contains``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:contains
        """
        return _FunctionCall(
            "cts:contains",
            (nodes, query),
        )

    @staticmethod
    def correlation(
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:correlation`` call.

        Returns the frequency-weighted correlation given a 2-way co-occurrence.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        value2 : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:correlation``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:correlation
        """
        return _FunctionCall(
            "cts:correlation",
            (value1, value2),
            (options, query, forest_ids),
        )

    @staticmethod
    def count_aggregate(
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:count-aggregate`` call.

        Returns the count of a value lexicon.

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

        Returns
        -------
        Expr
            Composable call to ``cts:count-aggregate``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:count-aggregate
        """
        return _FunctionCall(
            "cts:count-aggregate",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def covariance(
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:covariance`` call.

        Returns the frequency-weighted sample covariance given a 2-way co-
        occurrence.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        value2 : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:covariance``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:covariance
        """
        return _FunctionCall(
            "cts:covariance",
            (value1, value2),
            (options, query, forest_ids),
        )

    @staticmethod
    def covariance_p(
        value1,
        value2,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:covariance-p`` call.

        Returns the frequency-weighted covariance of the population given a
        2-way co-occurrence.

        Parameters
        ----------
        value1 : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        value2 : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:covariance-p``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:covariance-p
        """
        return _FunctionCall(
            "cts:covariance-p",
            (value1, value2),
            (options, query, forest_ids),
        )

    @staticmethod
    def deregister(id) -> Expr:
        """Build a composable ``cts:deregister`` call.

        Deregister a registered query, explicitly releasing the associated
        resources.

        Parameters
        ----------
        id : xs:unsignedLong
            A registered query identifier.

        Returns
        -------
        Expr
            Composable call to ``cts:deregister``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:deregister
        """
        return _FunctionCall(
            "cts:deregister",
            (id,),
        )

    @staticmethod
    def directory_query(uris, depth="1") -> Expr:
        """Build a composable ``cts:directory-query`` call.

        Returns a query matching documents in the directories with the given
        URIs.

        Parameters
        ----------
        uris : xs:string*
            One or more directory URIs.
        depth : xs:string?
            "1" for immediate children, "infinity" for all. If not supplied, depth is
            "1".

        Returns
        -------
        Expr
            Composable call to ``cts:directory-query``.

        Notes
        -----
        The directory URI should always have a trailing slash.

        Native reference: https://docs.marklogic.com/cts:directory-query
        """
        return _FunctionCall(
            "cts:directory-query",
            (uris,),
            (_depth(depth),),
        )

    @staticmethod
    def distinctive_terms(nodes, *, options=None) -> Expr:
        """Build a composable ``cts:distinctive-terms`` call.

        Return the most "relevant" terms in the model nodes (that is, the terms
        with the highest scores).

        Parameters
        ----------
        nodes : node()*
            Some model nodes.
        options : element()?
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

        Returns
        -------
        Expr
            Composable call to ``cts:distinctive-terms``.

        Notes
        -----
        Output Format

        cts:class element

        a sequence

        cts:term elements.

        cts:train

        cts:term element

        cts:query

        Native reference: https://docs.marklogic.com/cts:distinctive-terms
        """
        return _FunctionCall(
            "cts:distinctive-terms",
            (nodes,),
            (options,),
        )

    @staticmethod
    def document_format_query(format) -> Expr:
        """Build a composable ``cts:document-format-query`` call.

        Returns a query matching documents of a given format.

        Parameters
        ----------
        format : xs:string
            Case insensitve one of: "json","xml","text","binary". This will result in a
            XDMP-ARG exception in case of an invalid format.

        Returns
        -------
        Expr
            Composable call to ``cts:document-format-query``.

        Notes
        -----
        Requires MarkLogic 11 or later. Availability is checked by the server
        when the expression is evaluated, including in nested expressions.

        Native reference: https://docs.marklogic.com/cts:document-format-query
        """
        return _FunctionCall(
            "cts:document-format-query",
            (format,),
        )

    @staticmethod
    def document_fragment_query(query) -> Expr:
        """Build a composable ``cts:document-fragment-query`` call.

        Returns a query that matches all documents where $query matches any
        document fragment.

        Parameters
        ----------
        query : cts:query
            A query to be matched against any document fragment.

        Returns
        -------
        Expr
            Composable call to ``cts:document-fragment-query``.

        Notes
        -----
        A document fragment query enables you to cross fragment boundaries in an AND
        query, as shown in the second example below.

        Native reference: https://docs.marklogic.com/cts:document-fragment-query
        """
        return _FunctionCall(
            "cts:document-fragment-query",
            (query,),
        )

    @staticmethod
    def document_order(*, options=None) -> Expr:
        """Build a composable ``cts:document-order`` call.

        Creates a document-based ordering clause, for use as an option to
        cts:search.

        Parameters
        ----------
        options : xs:string*
            Options. Options include: "descending" Results should be returned in
            descending order of document. "ascending" Results should be returned in
            ascending order of document.

        Returns
        -------
        Expr
            Composable call to ``cts:document-order``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Native reference: https://docs.marklogic.com/cts:document-order
        """
        return _FunctionCall(
            "cts:document-order",
            (),
            (options,),
        )

    @staticmethod
    def document_permission_query(role, capability) -> Expr:
        """Build a composable ``cts:document-permission-query`` call.

        Returns a query matching documents with a given permission.

        Parameters
        ----------
        role : xs:string
            The role of the permission
        capability : xs:string
            The capability of the permission (read, update, node-update, insert,
            execute)

        Returns
        -------
        Expr
            Composable call to ``cts:document-permission-query``.

        Notes
        -----
        Requires MarkLogic 11 or later. Availability is checked by the server
        when the expression is evaluated, including in nested expressions.

        Native reference: https://docs.marklogic.com/cts:document-permission-query
        """
        return _FunctionCall(
            "cts:document-permission-query",
            (role, capability),
        )

    @staticmethod
    def document_query(uris) -> Expr:
        """Build a composable ``cts:document-query`` call.

        Returns a query matching documents with the given URIs.

        Parameters
        ----------
        uris : xs:string*
            One or more document URIs.

        Returns
        -------
        Expr
            Composable call to ``cts:document-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:document-query
        """
        return _FunctionCall(
            "cts:document-query",
            (uris,),
        )

    @staticmethod
    def document_root_query(root) -> Expr:
        """Build a composable ``cts:document-root-query`` call.

        Returns a query matching documents with a given root element.

        Parameters
        ----------
        root : xs:QName
            The root QName to query.

        Returns
        -------
        Expr
            Composable call to ``cts:document-root-query``.

        Notes
        -----
        Requires MarkLogic 11 or later. Availability is checked by the server
        when the expression is evaluated, including in nested expressions.

        Native reference: https://docs.marklogic.com/cts:document-root-query
        """
        return _FunctionCall(
            "cts:document-root-query",
            (_qname(root),),
        )

    @staticmethod
    def element_attribute_pair_geospatial_boxes(
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
    ) -> Expr:
        """Build a composable ``cts:element-attribute-pair-geospatial-boxes`` call.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more element QNames.
        longitude_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : xs:double*
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : xs:string*
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
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-boxes``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all boxes with
        included points may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then points from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple boxes or no boxes. The
        number of fragments skipped does not correspond to the number of boxes. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        box list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference:
        https://docs.marklogic.com/cts:element-attribute-pair-geospatial-boxes
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-boxes",
            (
                _qname(parent_element_names),
                _qname(latitude_names),
                _qname(longitude_names),
            ),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def element_attribute_pair_geospatial_query(
        element_name,
        latitude_attribute_names,
        longitude_attribute_names,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-pair-geospatial-query`` call.

        Returns a query matching elements by name which has specific attributes
        representing latitude and longitude values for a point contained within
        the given geographic box, circle, or polygon, or equal to the given
        point.

        Parameters
        ----------
        element_name : xs:QName*
            One or more parent element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches.
        latitude_attribute_names : xs:QName*
            One or more latitude attribute QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching latitude attribute in any point instance will be checked.
        longitude_attribute_names : xs:QName*
            One or more longitude attribute QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching longitude attribute in any point instance will be checked.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-query``.

        Notes
        -----
        The point value is expressed as the numerical values in the textual content of
        the named attributes.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        The point values and the boundary specifications are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary (that is, if the value of 'w' is
        greater than the value of 'e'), then the box crosses the anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference:
        https://docs.marklogic.com/cts:element-attribute-pair-geospatial-query
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-query",
            (
                _qname(element_name),
                _qname(latitude_attribute_names),
                _qname(longitude_attribute_names),
                regions,
            ),
            (options, _double(weight)),
        )

    @staticmethod
    def element_attribute_pair_geospatial_value_match(
        element_names,
        latitude_names,
        longitude_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build an ``element-attribute-pair-geospatial-value-match`` call.

        Returns values from the specified element attribute pair geospatial
        value lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        For finer control over the lexicon selection, use cts:value-match .

        Native reference:
        https://docs.marklogic.com/cts:element-attribute-pair-geospatial-value-match
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-value-match",
            (
                _qname(element_names),
                _qname(latitude_names),
                _qname(longitude_names),
                pattern,
            ),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_pair_geospatial_values(
        element_names,
        latitude_names,
        longitude_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-pair-geospatial-values`` call.

        Returns values from the specified element-attribute-pair geospatial
        value lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        start : cts:point?
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        When multiple element and/or child QNames are specified, then all possible
        element/child QName combinations are used to select the matching values. For
        finer control over the indexes, use cts:values .

        Native reference:
        https://docs.marklogic.com/cts:element-attribute-pair-geospatial-values
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-values",
            (_qname(element_names), _qname(latitude_names), _qname(longitude_names)),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_range_query(
        element_name,
        attribute_name,
        operator,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-range-query`` call.

        Constructs a query that matches element-attributes by name with a range-
        index entry equal to a given value.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        attribute_name : xs:QName*
            One or more attribute QNames to match. When multiple QNames are specified,
            the query matches if any QName matches.
        operator : xs:string
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : xs:anyAtomicType*
            Some values to match. When multiple values are specified, the query matches
            if any value matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-range-query``.

        Notes
        -----
        To constrain on a range of values, combine multiple element attribute range
        queries together using cts:and-query or another composable query constructor.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        The "cached-incremental" option can improve performance if you repeatedly
        perform range queries on date or dateTime values over a short range that does
        not vary widely over short period of time. To benefit, the operator should
        remain the same "direction" (<,<=, or >,>=) across calls, the bounding date or
        dateTime changes slightly across calls, and the query runs very frequently
        (multiple times per minute). Note that using this options creates significantly
        more cached queries than the "cached" option.

        The "cached-incremental" option has the following restrictions and interactions:
        The "min-occurs" and "max-occurs" options will be ignored if you use
        "cached-incremental" in unfiltered search. You can only use
        "score-function=zero" with "cached-incremental". The "cached-incremental" option
        behaves like "cached" if you are not querying date or dateTime values.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        For queries against a dateTime index, when $value is an xs:dayTimeDuration or
        xs:yearMonthDuration, the query is executed as an age query. $value is
        subtracted from fn:current-dateTime() to create an xs:dateTime used in the
        query. If there is more than one item in $value, they must all be the same type.

        Native reference: https://docs.marklogic.com/cts:element-attribute-range-query
        """
        return _FunctionCall(
            "cts:element-attribute-range-query",
            (_qname(element_name), _qname(attribute_name), _operator(operator), value),
            (options, _double(weight)),
        )

    @staticmethod
    def element_attribute_reference(element, attribute, *, options=None) -> Expr:
        """Build a composable ``cts:element-attribute-reference`` call.

        Creates a reference to an element attribute value lexicon, for use as a
        parameter to cts:value-tuples.

        Parameters
        ----------
        element : xs:QName
            An element QName.
        attribute : xs:QName
            An attribute QName.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (int, unsignedInt, long, unsignedLong,
            float, double, decimal, dateTime, time, date, gYearMonth, gYear, gMonth,
            gDay, yearMonthDuration, dayTimeDuration, string, anyURI, point, or
            long-lat-point) "collation= URI " Use the lexicon with the collation
            specified by URI . "nullable" Allow null values in tuples reported from
            cts:value-tuples when using this lexicon. "unchecked" Read the scalar type,
            collation and coordinate-system info only from the input. Do not check the
            definition against the context database. "coordinate-system= name " Create a
            reference to an index or lexicon based on the specified coordinate system.
            Allowed values: "wgs84", "wgs84/double", "raw", "raw/double". Only
            applicable if the index/lexicon value type is point or long-lat-point .
            "precision= value " Create a reference to an index or lexicon configured
            with the specified geospatial precision. Allowed values: float and double .
            Only applicable if the index/lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:element-attribute-reference
        """
        return _FunctionCall(
            "cts:element-attribute-reference",
            (_qname(element), _qname(attribute)),
            (options,),
        )

    @staticmethod
    def element_attribute_value_co_occurrences(
        element_name_1,
        attribute_name_1,
        element_name_2,
        attribute_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-value-co-occurrences`` call.

        Returns value co-occurrences from the specified element or element-
        attribute value lexicon(s).

        Parameters
        ----------
        element_name_1 : xs:QName
            An element QName.
        attribute_name_1 : xs:QName?
            An attribute QName or empty sequence. The empty sequence specifies an
            element lexicon.
        element_name_2 : xs:QName
            An element QName.
        attribute_name_2 : xs:QName?
            An attribute QName or empty sequence. The empty sequence specifies an
            element lexicon.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-co-occurrences``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the co-occurrences returned by this function,
        use fn:subsequence on the output, rather than the "skip" option. The "skip"
        option is based on fragments matching the query parameter (if present), not on
        occurrences. A fragment matched by query might contain multiple occurrences or
        no occurrences. The number of fragments skipped does not correspond to the
        number of values. Also, the skip is applied to the relevance ordered query
        matches, not to the ordered result list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference:
        https://docs.marklogic.com/cts:element-attribute-value-co-occurrences
        """
        return _FunctionCall(
            "cts:element-attribute-value-co-occurrences",
            (
                _qname(element_name_1),
                _qname(attribute_name_1),
                _qname(element_name_2),
                _qname(attribute_name_2),
            ),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_value_geospatial_co_occurrences(
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
    ) -> Expr:
        """Build an ``element-attribute-value-geospatial-co-occurrences`` call.

        Returns value co-occurrences from the specified element-attribute value
        lexicon with the specified geospatial lexicon.

        Parameters
        ----------
        element_name_1 : xs:QName
            A QName identifying the parent element of the first lexicon.
        attribute_name_1 : xs:QName?
            A QName identifying an attribute of element-name-1 .
        geo_element_name : xs:QName
            A QName identifying the second lexicon, which must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the coord-child-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in coord-child-name-1 and coord-child-name-2 .
        coord_child_name_1 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name identifies an element or JSON property
            geospatial lexicon.
        coord_child_name_2 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable ``cts:element-attribute-value-geospatial-co-occurrences``
            call.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        If "sample= N " is not specfied in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference:
        https://docs.marklogic.com/cts:element-attribute-value-geospatial-co-occurrences
        """
        return _FunctionCall(
            "cts:element-attribute-value-geospatial-co-occurrences",
            (
                _qname(element_name_1),
                _qname(attribute_name_1),
                _qname(geo_element_name),
            ),
            (
                _qname(coord_child_name_1) if coord_child_name_1 is not None else None,
                _qname(coord_child_name_2) if coord_child_name_2 is not None else None,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def element_attribute_value_match(
        element_names,
        attribute_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-value-match`` call.

        Returns values from the specified element-attribute value lexicon(s)
        that match the specified pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a range index with that collation does not exist, an error
        is thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        When multiple element and/or attribute QNames are specified, then all possible
        element/attribute QName combinations are used to select the matching values.

        Native reference: https://docs.marklogic.com/cts:element-attribute-value-match
        """
        return _FunctionCall(
            "cts:element-attribute-value-match",
            (_qname(element_names), _qname(attribute_names), pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_value_query(
        element_name,
        attribute_name,
        text,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-value-query`` call.

        Returns a query matching elements by name with attributes by name with
        text content equal a given phrase.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        attribute_name : xs:QName*
            One or more attribute QNames to match. When multiple QNames are specified,
            the query matches if any QName matches.
        text : xs:string*
            One or more attribute values to match. When multiple strings are specified,
            the query matches if any string matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        When you use the "exact" option, you should also enable "fast case sensitive
        searches" and "fast diacritic sensitive searches" in your database
        configuration.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        When multiple element and/or attribute QNames are specified, then all possible
        element/attribute QName combinations are used to select the matching values.

        Native reference: https://docs.marklogic.com/cts:element-attribute-value-query
        """
        return _FunctionCall(
            "cts:element-attribute-value-query",
            (_qname(element_name), _qname(attribute_name), text),
            (options, _double(weight)),
        )

    @staticmethod
    def element_attribute_value_ranges(
        element_names,
        attribute_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-value-ranges`` call.

        Returns value ranges from the specified element-attribute value
        lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-ranges``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a range index with that collation does not exist, an error
        is thrown.

        If "sample= N " is not specified in the options parameter, then ranges with all
        included values may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        When multiple element and/or attribute QNames are specified, then all possible
        element/attribute QName combinations are used to select the matching values.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        results list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-attribute-value-ranges
        """
        return _FunctionCall(
            "cts:element-attribute-value-ranges",
            (_qname(element_names), _qname(attribute_names)),
            (bounds, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_values(
        element_names,
        attribute_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-values`` call.

        Returns values from the specified element-attribute value lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        start : xs:anyAtomicType?
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a range index with that collation does not exist, an error
        is thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        When multiple element and/or attribute QNames are specified, then all possible
        element/attribute QName combinations are used to select the matching values.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-attribute-values
        """
        return _FunctionCall(
            "cts:element-attribute-values",
            (_qname(element_names), _qname(attribute_names)),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_word_match(
        element_names,
        attribute_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-word-match`` call.

        Returns words from the specified element-attribute word lexicon(s) that
        match a wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-word-match``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        When multiple element and/or attribute QNames are specified, then all possible
        element/attribute QName combinations are used to select the matching values.

        Native reference: https://docs.marklogic.com/cts:element-attribute-word-match
        """
        return _FunctionCall(
            "cts:element-attribute-word-match",
            (_qname(element_names), _qname(attribute_names), pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_attribute_word_query(
        element_name,
        attribute_name,
        text,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-word-query`` call.

        Returns a query matching elements by name with attributes by name with
        text content containing a given phrase.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        attribute_name : xs:QName*
            One or more attribute QNames to match. When multiple QNames are specified,
            the query matches if any QName matches.
        text : xs:string*
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
            "lexicon-expand= value " The value is one of full , prefix-postfix , off ,
            or heuristic (the default is heuristic ). An option with a value of
            lexicon-expand=full specifies that wildcards are resolved by expanding the
            pattern to words in a lexicon (if there is one available), and turning into
            a series of cts:word-queries , even if this takes a long time to evaluate.
            An option with a value of lexicon-expand=prefix-postfix specifies that
            wildcards are resolved by expanding the pattern to the pre- and postfixes of
            the words in the word lexicon (if there is one), and turning the query into
            a series of character queries, even if it takes a long time to evaluate. An
            option with a value of lexicon-expand=off specifies that wildcards are only
            resolved by looking up character patterns in the search pattern index, not
            in the lexicon. An option with a value of lexicon-expand=heuristic , which
            is the default, specifies that wildcards are resolved by using a series of
            internal rules, such as estimating the number of lexicon entries that need
            to be scanned, seeing if the estimate crosses certain thresholds, and (if
            appropriate), using another way besides lexicon expansion to resolve the
            query. * "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-word-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Native reference: https://docs.marklogic.com/cts:element-attribute-word-query
        """
        return _FunctionCall(
            "cts:element-attribute-word-query",
            (_qname(element_name), _qname(attribute_name), text),
            (options, _double(weight)),
        )

    @staticmethod
    def element_attribute_words(
        element_names,
        attribute_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-attribute-words`` call.

        Returns words from the specified element-attribute word lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        attribute_names : xs:QName*
            One or more attribute QNames.
        start : xs:string?
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-words``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        When multiple element and/or attribute QNames are specified, then all possible
        element/attribute QName combinations are used to select the matching values.

        When run without a $query parameter and as a user with the admin role, the word
        lexicon functions return results that might include words from deleted
        fragments. However, when run as a user with the admin role and without a $query
        parameter, the word lexicon functions run faster (because they do not need to
        look up where each word comes from). It is therefore faster to run word lexicon
        functions as an admin user without passing a $query parameter.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-attribute-words
        """
        return _FunctionCall(
            "cts:element-attribute-words",
            (_qname(element_names), _qname(attribute_names)),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_child_geospatial_boxes(
        parent_element_names,
        child_element_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-child-geospatial-boxes`` call.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        child_element_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : xs:double*
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : xs:string*
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
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-boxes``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        If "sample= N " is not specfied in the options parameter, then all boxes with
        included points may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "truncate= N " is not specfied in the options parameter, then points from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple boxes or no boxes. The
        number of fragments skipped does not correspond to the number of boxes. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        box list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-boxes
        """
        return _FunctionCall(
            "cts:element-child-geospatial-boxes",
            (_qname(parent_element_names), _qname(child_element_names)),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def element_child_geospatial_query(
        parent_element_name,
        child_element_names,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-child-geospatial-query`` call.

        Returns a query matching elements by name which has specific element
        children representing latitude and longitude values for a point
        contained within the given geographic box, circle, or polygon, or equal
        to the given point.

        Parameters
        ----------
        parent_element_name : xs:QName*
            One or more parent element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches.
        child_element_names : xs:QName*
            One or more child element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching latitude child in any point instance will be checked. The element
            must specify both latitude and longitude coordinates.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= string " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "units= value
            " Measure distance and the radii of circles in the specified units. Allowed
            values: miles (default), km , feet , meters . "boundaries-included" Points
            on boxes', circles', and polygons' boundaries are counted as matching. This
            is the default. "boundaries-excluded" Points on boxes', circles', and
            polygons' boundaries are not counted as matching.
            "boundaries-latitude-excluded" Points on boxes' latitude boundaries are not
            counted as matching. "boundaries-longitude-excluded" Points on boxes'
            longitude boundaries are not counted as matching.
            "boundaries-south-excluded" Points on the boxes' southern boundaries are not
            counted as matching. "boundaries-west-excluded" Points on the boxes' western
            boundaries are not counted as matching. "boundaries-north-excluded" Points
            on the boxes' northern boundaries are not counted as matching.
            "boundaries-east-excluded" Points on the boxes' eastern boundaries are not
            counted as matching. "boundaries-circle-excluded" Points on circles'
            boundary are not counted as matching. "boundaries-endpoints-excluded" Points
            on linestrings' boundary (the endpoints) are not counted as matching.
            "cached" Cache the results of this query in the list cache. "uncached" Do
            not cache the results of this query in the list cache. "type=long-lat-point"
            Specifies the format for the point in the data as longitude first, latitude
            second. "type=point" Specifies the format for the point in the data as
            latitude first, longitude second. This is the default format.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-query``.

        Notes
        -----
        The point value is expressed in the content of the element as a child of
        numbers, separated by whitespace and punctuation (excluding decimal points and
        sign characters).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Point values and boundary specifications of boxes are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-query
        """
        return _FunctionCall(
            "cts:element-child-geospatial-query",
            (_qname(parent_element_name), _qname(child_element_names), regions),
            (options, _double(weight)),
        )

    @staticmethod
    def element_child_geospatial_value_match(
        element_names,
        child_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-child-geospatial-value-match`` call.

        Returns values from the specified element child geospatial value
        lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames identifying the parent element(s).
        child_names : xs:QName*
            One or more child element QNames.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        For finer control over the lexicon selection, use cts:value-match .

        Native reference:
        https://docs.marklogic.com/cts:element-child-geospatial-value-match
        """
        return _FunctionCall(
            "cts:element-child-geospatial-value-match",
            (_qname(element_names), _qname(child_names), pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_child_geospatial_values(
        element_names,
        child_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-child-geospatial-values`` call.

        Returns values from the specified element-child geospatial value
        lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        child_names : xs:QName*
            One or more child element QNames.
        start : cts:point?
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        When multiple element and/or child QNames are specified, then all possible
        element/child QName combinations are used to select the matching values.

        Native reference: https://docs.marklogic.com/cts:element-child-geospatial-values
        """
        return _FunctionCall(
            "cts:element-child-geospatial-values",
            (_qname(element_names), _qname(child_names)),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_geospatial_boxes(
        element_names,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-geospatial-boxes`` call.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : xs:double*
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : xs:string*
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
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-boxes``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all boxes with
        included points may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then points from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple boxes or no boxes. The
        number of fragments skipped does not correspond to the number of boxes. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        box list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-geospatial-boxes
        """
        return _FunctionCall(
            "cts:element-geospatial-boxes",
            (_qname(element_names),),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def element_geospatial_query(
        element_name,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-geospatial-query`` call.

        Returns a query matching elements by name whose content represents a
        point contained within the given geographic box, circle, or polygon, or
        equal to the given point.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "type=long-lat-point" Specifies the format for the point
            in the data as longitude first, latitude second. "type=point" Specifies the
            format for the point in the data as latitude first, longitude second. This
            is the default format. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-query``.

        Notes
        -----
        The point value is expressed in the content of the element as a pair of numbers,
        separated by whitespace and punctuation (excluding decimal points and sign
        characters).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Point and region coordinates are interpreted according to the governing
        coordinate system of the query. When using a geographic coordinate system such
        as wgs84 or wgs84/double the following also applies:

        Southern latitudes and Western longitudes take negative values. Longitudes are
        wrapped to the range (-180,+180). Latitudes are clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:element-geospatial-query
        """
        return _FunctionCall(
            "cts:element-geospatial-query",
            (_qname(element_name), regions),
            (options, _double(weight)),
        )

    @staticmethod
    def element_geospatial_value_match(
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-geospatial-value-match`` call.

        Returns values from the specified element geospatial value lexicon(s)
        that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-geospatial-value-match
        """
        return _FunctionCall(
            "cts:element-geospatial-value-match",
            (_qname(element_names), pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_geospatial_values(
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-geospatial-values`` call.

        Returns values from the specified element geospatial value lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : cts:point?
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-geospatial-values
        """
        return _FunctionCall(
            "cts:element-geospatial-values",
            (_qname(element_names),),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_pair_geospatial_boxes(
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
    ) -> Expr:
        """Build a composable ``cts:element-pair-geospatial-boxes`` call.

        Returns boxes derived from the specified element point lexicon(s).

        Parameters
        ----------
        parent_element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more element QNames.
        longitude_names : xs:QName*
            One or more element QNames.
        latitude_bounds : xs:double*
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : xs:double*
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : xs:string*
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
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-boxes``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all boxes with
        included points may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then points from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple boxes or no boxes. The
        number of fragments skipped does not correspond to the number of boxes. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        box list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-boxes
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-boxes",
            (
                _qname(parent_element_names),
                _qname(latitude_names),
                _qname(longitude_names),
            ),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def element_pair_geospatial_query(
        element_name,
        latitude_element_names,
        longitude_element_names,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-pair-geospatial-query`` call.

        Returns a query matching elements by name which has specific element
        children representing latitude and longitude values for a point
        contained within the given geographic box, circle, or polygon, or equal
        to the given point.

        Parameters
        ----------
        element_name : xs:QName*
            One or more parent element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches.
        latitude_element_names : xs:QName*
            One or more latitude element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching latitude child in any point instance will be checked.
        longitude_element_names : xs:QName*
            One or more longitude element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching longitude child in any point instance will be checked.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-query``.

        Notes
        -----
        The point value is expressed in the content of the latitude and longitude
        elements (the latitude value in the latitude element, and the longitude value in
        the longitude element).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Point values and boundary specifications of boxes are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-query
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-query",
            (
                _qname(element_name),
                _qname(latitude_element_names),
                _qname(longitude_element_names),
                regions,
            ),
            (options, _double(weight)),
        )

    @staticmethod
    def element_pair_geospatial_value_match(
        element_names,
        latitude_names,
        longitude_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-pair-geospatial-value-match`` call.

        Returns values from the specified element pair geospatial value
        lexicon(s) that match the specified wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        For finer control over the lexicons election, use cts:value-match .

        Native reference:
        https://docs.marklogic.com/cts:element-pair-geospatial-value-match
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-value-match",
            (
                _qname(element_names),
                _qname(latitude_names),
                _qname(longitude_names),
                pattern,
            ),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_pair_geospatial_values(
        element_names,
        latitude_names,
        longitude_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-pair-geospatial-values`` call.

        Returns values from the specified element-pair geospatial value
        lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames identifying the parent element of the latitude
            and longitude elements.
        latitude_names : xs:QName*
            One or more latitude element QNames.
        longitude_names : xs:QName*
            One or more longitude element QNames.
        start : cts:point?
            A starting value. If the parameter value is not in the lexicon, then the
            values are returned beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by this query, and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specfied in the options parameter, then values from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        When multiple element and/or child QNames are specified, then all possible
        element/child QName combinations are used to select the matching values. If an
        index does not exist for any parent-lat-lon element combination, an exception is
        thrown. For finer control over the expected index configuration, use cts:values
        .

        Native reference: https://docs.marklogic.com/cts:element-pair-geospatial-values
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-values",
            (_qname(element_names), _qname(latitude_names), _qname(longitude_names)),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_query(element_name, query) -> Expr:
        """Build a composable ``cts:element-query`` call.

        Constructs a query that matches elements by name with the content
        constrained by the query given in the second parameter.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        query : cts:query
            A query for the element to match. If a string is entered, the string is
            treated as a cts:word-query of the specified string.

        Returns
        -------
        Expr
            Composable call to ``cts:element-query``.

        Notes
        -----
        Enabling both the word position and element position indexes ("word position"
        and "element word position" in the database configuration screen of the Admin
        Interface) will speed up query performance for many queries that use
        cts:element-query . The position indexes enable MarkLogic Server to eliminate
        many false-positive results, which can reduce disk I/O and processing, thereby
        speeding the performance of many queries. The amount of benefit will vary
        depending on your data.

        You can query for the existence of an element by specifying an empty
        cts:and-query as the second parameter. For example, the following will match any
        instance of the specified element:

        cts:element-query(xs:QName("my-element"), cts:and-query( () ))

        Native reference: https://docs.marklogic.com/cts:element-query
        """
        return _FunctionCall(
            "cts:element-query",
            (_qname(element_name), query),
        )

    @staticmethod
    def element_range_query(
        element_name,
        operator,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-range-query`` call.

        Constructs a query that matches elements by name with range index entry
        equal to a given value.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        operator : xs:string
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : xs:anyAtomicType*
            One or more element values to match. When multiple values are specified, the
            query matches if any value matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:element-range-query``.

        Notes
        -----
        To constrain on a range of values, combine multiple element range queries
        together using cts:and-query or any of the composable query constructors, as in
        the last part of the example below.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        The "cached-incremental" option can improve performance if you repeatedly
        perform range queries on date or dateTime values over a short range that does
        not vary widely over short period of time. To benefit, the operator should
        remain the same "direction" (<,<=, or >,>=) across calls, the bounding date or
        dateTime changes slightly across calls, and the query runs very frequently
        (multiple times per minute). Note that using this options creates significantly
        more cached queries than the "cached" option.

        The "cached-incremental" option has the following restrictions and interactions:
        The "min-occurs" and "max-occurs" options will be ignored if you use
        "cached-incremental" in unfiltered search. You can only use
        "score-function=zero" with "cached-incremental". The "cached-incremental" option
        behaves like "cached" if you are not querying date or dateTime values.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        For queries against a dateTime index, when $value is an xs:dayTimeDuration or
        xs:yearMonthDuration, the query is executed as an age query. $value is
        subtracted from fn:current-dateTime() to create an xs:dateTime used in the
        query. If there is more than one item in $value, they must all be the same type.

        Native reference: https://docs.marklogic.com/cts:element-range-query
        """
        return _FunctionCall(
            "cts:element-range-query",
            (_qname(element_name), _operator(operator), value),
            (options, _double(weight)),
        )

    @staticmethod
    def element_reference(element, *, options=None) -> Expr:
        """Build a composable ``cts:element-reference`` call.

        Creates a reference to an element value lexicon, for use as a parameter
        to cts:value-tuples, temporal:axis-create, or any other function that
        takes an index reference.

        Parameters
        ----------
        element : xs:QName
            An element QName.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (int, unsignedInt, long, unsignedLong,
            float, double, decimal, dateTime, time, date, gYearMonth, gYear, gMonth,
            gDay, yearMonthDuration, dayTimeDuration, string, anyURI, point, or
            long-lat-point) "collation= URI " Use the lexicon with the collation
            specified by URI . "nullable" Allow null values in tuples reported from
            cts:value-tuples when using this lexicon. "unchecked" Read the scalar type,
            collation and coordinate-system info only from the input. Do not check the
            definition against the context database. "coordinate-system= name " Create a
            reference to an index or lexicon based on the specified coordinate system.
            Allowed values: "wgs84", "wgs84/double", "raw", "raw/double". Only
            applicable if the index/lexicon value type is point or long-lat-point .
            "precision= value " Create a reference to an index or lexicon configured
            with the specified geospatial precision. Allowed values: float and double .
            Only applicable if the index/lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.

        Returns
        -------
        Expr
            Composable call to ``cts:element-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:element-reference
        """
        return _FunctionCall(
            "cts:element-reference",
            (_qname(element),),
            (options,),
        )

    @staticmethod
    def element_value_co_occurrences(
        element_name_1,
        element_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-value-co-occurrences`` call.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified element value
        lexicon(s).

        Parameters
        ----------
        element_name_1 : xs:QName
            An element QName.
        element_name_2 : xs:QName
            An element QName.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-co-occurrences``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the co-occurrences returned by this function,
        use fn:subsequence on the output, rather than the "skip" option. The "skip"
        option is based on fragments matching the query parameter (if present), not on
        values. A fragment matched by query might contain multiple occurrences or no
        occurrences. The number of fragments skipped does not correspond to the number
        of values. Also, the skip is applied to the relevance ordered query matches, not
        to the ordered co-occurrences list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-value-co-occurrences
        """
        return _FunctionCall(
            "cts:element-value-co-occurrences",
            (_qname(element_name_1), _qname(element_name_2)),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_value_geospatial_co_occurrences(
        element_name_1,
        geo_element_name,
        *,
        coord_child_name_1=None,
        coord_child_name_2=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-value-geospatial-co-occurrences`` call.

        Returns value co-occurrences from the specified element value lexicon
        with the specified geospatial lexicon.

        Parameters
        ----------
        element_name_1 : xs:QName
            A QName identifying the first lexicon. If this is a geospatial lexicon, it
            can only be an element geospatial lexicon. You should usually use
            cts:geospatial-co-occurrences to find co-occurrences between two geospatial
            lexicons.
        geo_element_name : xs:QName
            A QName identifying the second lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the coord-child-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in coord-child-name-1 and coord-child-name-2 .
        coord_child_name_1 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name identifies an element or JSON property
            geospatial lexicon.
        coord_child_name_2 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-geospatial-co-occurrences``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        If "sample= N " is not specfied in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference:
        https://docs.marklogic.com/cts:element-value-geospatial-co-occurrences
        """
        return _FunctionCall(
            "cts:element-value-geospatial-co-occurrences",
            (_qname(element_name_1), _qname(geo_element_name)),
            (
                _qname(coord_child_name_1) if coord_child_name_1 is not None else None,
                _qname(coord_child_name_2) if coord_child_name_2 is not None else None,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def element_value_match(
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-value-match`` call.

        Returns values from the specified element value lexicon(s) that match
        the specified wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a range index with that collation does not exist, an error
        is thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Native reference: https://docs.marklogic.com/cts:element-value-match
        """
        return _FunctionCall(
            "cts:element-value-match",
            (_qname(element_names), pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_value_query(
        element_name,
        text=None,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:element-value-query`` call.

        Returns a query matching elements by name with text content equal a
        given phrase.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        text : xs:string*
            One or more element values to match. When multiple strings are specified,
            the query matches if any string matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        When you use the "exact" option, you should also enable "fast case sensitive
        searches" and "fast diacritic sensitive searches" in your database
        configuration.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Note that the text content for the value in a cts:element-value-query is treated
        the same as a phrase in a cts:word-query , where the phrase is the element
        value. Therefore, any wildcard and/or stemming rules are treated like a phrase.
        For example, if you have an element value of "hello friend" with wildcarding
        enabled for a query, a cts:element-value-query for "he*" will not match because
        the wildcard matches do not span word boundaries, but a cts:element-value-query
        for "hello *" will match. A search for "*" will match, because a "*" wildcard by
        itself is defined to match the value. Similarly, stemming rules are applied to
        each term, so a search for "hello friends" would match when stemming is enabled
        for the query because "friends" matches "friend". For an example, see the fourth
        example that follows.

        Similarly, because a "*" wildcard by itself is defined to match the value, the
        following query will match any element with the QName my-element , regardless of
        the wildcard indexes enabled in the database configuration:
        cts:element-value-query(xs:QName("my-element"), "*", "wildcarded")

        Native reference: https://docs.marklogic.com/cts:element-value-query
        """
        return _FunctionCall(
            "cts:element-value-query",
            (_qname(element_name),),
            (text, options, _double(weight)),
        )

    @staticmethod
    def element_value_ranges(
        element_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-value-ranges`` call.

        Returns value ranges from the specified element value lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-ranges``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then ranges with all
        included values may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        results list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-value-ranges
        """
        return _FunctionCall(
            "cts:element-value-ranges",
            (_qname(element_names),),
            (bounds, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_values(
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-values`` call.

        Returns values from the specified element value lexicon(s).

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames. If you specify multiple lexicons, they must all
            be over the same value type (string, int, etc.).
        start : xs:anyAtomicType?
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the query parameter are included. If a query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-values
        """
        return _FunctionCall(
            "cts:element-values",
            (_qname(element_names),),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_walk(node, element, expr) -> Expr:
        """Build a composable ``cts:element-walk`` call.

        Returns a copy of the node, replacing any elements found with the
        specified expression.

        Parameters
        ----------
        node : node()
            A node to run the walk over. The node must be either a document node or an
            element node; it cannot be a text node.
        element : xs:QName*
            The name of elements to replace.
        expr : item()*
            An expression with which to replace each match. You can use the variables
            $cts:node and $cts:action (described below) in the expression.

        Returns
        -------
        Expr
            Composable call to ``cts:element-walk``.

        Notes
        -----
        There are two built-in variables to represent an element match. These variables
        can be used inline in the expression parameter.

        $cts:node as element() The matching element node. $cts:action as xs:string Use
        xdmp:set on this to specify what should happen next "continue" (default) Walk
        the next match. If there are no more matches, return all evaluation results.
        "skip" Skip walking any more matches and return all evaluation results. "break"
        Stop walking matches and return all evaluation results.

        Native reference: https://docs.marklogic.com/cts:element-walk
        """
        return _FunctionCall(
            "cts:element-walk",
            (node, _qname(element), expr),
        )

    @staticmethod
    def element_word_match(
        element_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-word-match`` call.

        Returns words from the specified element word lexicon(s) that match a
        wildcard pattern.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        pattern : xs:string?
            Wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-word-match``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Only words that can be matched with element-word-query are included. That is,
        only words present in immediate text node children of the specified element as
        well as any text node children of child elements defined in the Admin Interface
        as element-word-query-throughs or phrase-throughs.

        Native reference: https://docs.marklogic.com/cts:element-word-match
        """
        return _FunctionCall(
            "cts:element-word-match",
            (_qname(element_names), pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def element_word_query(element_name, text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:element-word-query`` call.

        Returns a query matching elements by name with text content containing a
        given phrase.

        Parameters
        ----------
        element_name : xs:QName*
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        text : xs:string*
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard. "no-limit-check" is default, if neither "limit-check" nor
            "no-limit-check" is explicitly specified.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:element-word-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Relevance adjustment for the "distance-weight" option depends on the closest
        proximity of any two matches of the query. For example,
        cts:element-word-query(xs:QName("p"),("dog","cat"),("distance-weight=10")) will
        adjust relevance based on the distance between the closest pair of matches of
        either "dog" or "cat" within an element named "p" (the pair may consist only of
        matches of "dog", only of matches of "cat", or a match of "dog" and a match of
        "cat").

        Native reference: https://docs.marklogic.com/cts:element-word-query
        """
        return _FunctionCall(
            "cts:element-word-query",
            (_qname(element_name), text),
            (options, _double(weight)),
        )

    @staticmethod
    def element_words(
        element_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:element-words`` call.

        Returns words from the specified element word lexicon.

        Parameters
        ----------
        element_names : xs:QName*
            One or more element QNames.
        start : xs:string?
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:element-words``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        Only words that can be matched with element-word-query are included. That is,
        only words present in immediate text node children of the specified element as
        well as any text node children of child elements defined in the Admin Interface
        as element-word-query-throughs or phrase-throughs.

        When run without a $query parameter and as a user with the admin role, the word
        lexicon functions return results that might include words from deleted
        fragments. However, when run as a user with the admin role and without a $query
        parameter, the word lexicon functions run faster (because they do not need to
        look up where each word comes from). It is therefore faster to run word lexicon
        functions as an admin user without passing a $query parameter.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:element-words
        """
        return _FunctionCall(
            "cts:element-words",
            (_qname(element_names),),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def entity(id, normalized_text, text, type) -> Expr:
        """Build a composable ``cts:entity`` call.

        Returns a cts:entity object.

        Parameters
        ----------
        id : xs:string
            A unique ID for the entity. A unique entity may have multiple entries in the
            dictionary with different matching words: the unique ID ties them all
            together. For entities created from a SKOS ontology this could be the URI of
            the Concept . The variable $cts:entity-id in cts:entity-highlight and
            cts:entity-walk will be filled in with this ID for each matching entity.
        normalized_text : xs:string
            The normalized form of the entity. For entities created from a SKOS ontology
            this could be the preferred label of the Concept . The variable
            $cts:normalized-text in cts:entity-highlight and cts:entity-walk will be
            filled in with this form for each matching entity.
        text : xs:string
            The word (or phrase) to match during entity extraction. This will be an
            exact match, unless the dictionary was created with the "case-insensitive"
            option, in which case the string is matched with case folding. For entities
            created from a SKOS ontology this could be a label or alternative label for
            the Concept .
        type : xs:string
            The type of the entity. For entities created from a SKOS ontology this could
            be the id of the top concept for the matching Concept , or its preferred
            label. The variable $cts:entity-type in cts:entity-highlight and
            cts:entity-walk will be filled in with this type for each matching entity.

        Returns
        -------
        Expr
            Composable call to ``cts:entity``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:entity
        """
        return _FunctionCall(
            "cts:entity",
            (id, normalized_text, text, type),
        )

    @staticmethod
    def entity_dictionary(entities, *, options=None) -> Expr:
        """Build a composable ``cts:entity-dictionary`` call.

        Returns a cts:entity-dictionary object.

        Parameters
        ----------
        entities : cts:entity*
            The entities to put into the dictionary.
        options : xs:string*
            Dictionary building options. The default is case-sensitive, allow-overlaps,
            and whole-words. Options include: "case-sensitive" Entity names are
            case-sensitive. "case-insensitive" Entity names are case-insensitive.
            "whole-words" Require that matches align with token boundaries.
            "partial-words" Allow matches to fall within token boundaries.
            "allow-overlaps" Allow overlapping entity labels. "remove-overlaps" Remove
            overlapping entity labels.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-dictionary``.

        Notes
        -----
        Only one of "case-sensitive" and "case-insensitive", "whole-words" and
        "partial-words", and "allow-overlaps" and "remove-overlaps" is permitted. It is
        strongly recommended that the defaults be used.

        Use this method when creating ad hoc entity dictionaries, or as a prelude to
        saving the entity dictionary to the database.

        Native reference: https://docs.marklogic.com/cts:entity-dictionary
        """
        return _FunctionCall(
            "cts:entity-dictionary",
            (entities,),
            (options,),
        )

    @staticmethod
    def entity_dictionary_get(uri) -> Expr:
        """Build a composable ``cts:entity-dictionary-get`` call.

        Retrieve an entity dictionary previously cached in the database.

        Parameters
        ----------
        uri : xs:string
            URI of a previously saved entity dictionary.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-dictionary-get``.

        Notes
        -----
        XDMP-NOSUCHDICT

        Native reference: https://docs.marklogic.com/cts:entity-dictionary-get
        """
        return _FunctionCall(
            "cts:entity-dictionary-get",
            (uri,),
        )

    @staticmethod
    def entity_dictionary_parse(contents, *, options=None) -> Expr:
        """Build a composable ``cts:entity-dictionary-parse`` call.

        Construct a cts:entity-dictionary object by parsing it from a formatted
        string.

        Parameters
        ----------
        contents : xs:string*
            The dictionary entries to parse. Each line (or string) must consist of four
            tab-delimited fields: The entity ID, the normalized form of the entity, the
            word or phrase to match during entity identification, and the entity type.
            For more details about the fields, see cts:entity . Multiple formatted
            strings can be passed in and they will be combined into a single dictionary
            object.
        options : xs:string*
            Dictionary building options. The default is case-sensitive, allow-overlaps,
            and whole-words. Options include: "case-sensitive" Entity names are
            case-sensitive. "case-insensitive" Entity names are case-insensitive.
            "whole-words" Require that matches align with token boundaries.
            "partial-words" Allow matches to fall within token boundaries.
            "allow-overlaps" Allow overlapping entity labels. "remove-overlaps" Remove
            overlapping entity labels.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-dictionary-parse``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:entity-dictionary-parse
        """
        return _FunctionCall(
            "cts:entity-dictionary-parse",
            (contents,),
            (options,),
        )

    @staticmethod
    def entity_highlight(node, expr, *, dict=None) -> Expr:
        """Build a composable ``cts:entity-highlight`` call.

        Returns a copy of the node, replacing any entities found with the
        specified expression.

        Parameters
        ----------
        node : node()
            A node to run entity highlight on. The node must be either a document node
            or an element node; it cannot be a text node.
        expr : item()*
            An expression with which to replace each match. You can use the variables
            $cts:text , $cts:node , $cts:entity-type and $cts:normalized-text ,
            $cts:start , and $cts:action (described below) in the expression.
        dict : cts:entity-dictionary
            The entity dictionary to use for matching entities in the text of the input
            node. If you omit this parameter, the default entity dictionary is used. (No
            default dictionaries currently exist.) See the Usage Notes for details.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-highlight``.

        Notes
        -----
        In addition to a valid Entity Enrichment license key, this function requires
        that you have installed the Entity Enrichment package. For details on installing
        the Entity Enrichment package, see the Installation Guide and the "Marking Up
        Documents With Entity Enrichment" chapter of the Search Developer's Guide .

        There are six built-in variables to represent an entity match. These variables
        can be used inline in the expression parameter.

        $cts:text as xs:string The matched text. $cts:node as text() The node containing
        the matched text. $cts:start as xs:integer The string-length position of the
        first character of $cts:text in $cts:node . Therefore, the following always
        returns true: fn:substring($cts:node, $cts:start, fn:string-length($cts:text))
        eq $cts:text $cts:action as xs:string Use xdmp:set on this to specify what
        should happen next "continue" (default) Walk the next match. If there are no
        more matches, return all evaluation results. "skip" Skip walking any more
        matches and return all evaluation results. "break" Stop walking matches and
        return all evaluation results. $cts:entity-type as xs:string The type of the
        matching entity. $cts:normalized-text as xs:string The normalized entity text
        (only applicable for some languages).

        The following are the entity types returned from the $cts:entity-type built-in
        variable (in alphabetical order):

        FACILITY A place used as a facility. GPE Geo-political entity. Differs from
        location because it has a person-made aspect to it (for example, California is a
        GPE because its boundaries were defined by a government).
        IDENTIFIER:CREDIT_CARD_NUM A number identifying a credit card number.
        IDENTIFIER:DISTANCE A number identifying a distance. IDENTIFIER:EMAIL Identifies
        an email address. IDENTIFIER:LATITUDE_LONGITUDE Latitude and longitude
        coordinates. IDENTIFIER:MONEY Identifies currency (dollars, euros, and so on).
        IDENTIFIER:NUMBER Identifies a number. IDENTIFIER:PERSONAL_ID_NUM A number
        identifying a social security number or other ID number. IDENTIFIER:PHONE_NUMBER
        A number identifying a telephone number. IDENTIFIER:URL Identifies a web site
        address (URL). IDENTIFIER:UTM Identifies Universal Transverse Mercator
        coordinates. LOCATION A geographic location (Mount Everest, for example).
        NATIONALITY The nationality of someone or something (for example, American).
        ORGANIZATION An organization. PERSON A person. RELIGION A religion.
        TEMPORAL:DATE Date-related. TEMPORAL:TIME Time-related. TITLE Appellation or
        honorific associated with a person. URL A URL on the world wide web. UTM A point
        in the Universal Transverse Mercator (UTM) coordinate system.

        Native reference: https://docs.marklogic.com/cts:entity-highlight
        """
        return _FunctionCall(
            "cts:entity-highlight",
            (node, expr),
            (dict,),
        )

    @staticmethod
    def entity_walk(node, expr, *, dict=None) -> Expr:
        """Build a composable ``cts:entity-walk`` call.

        Walk an XML document or element node, evaluating an expression against
        any matching entities.

        Parameters
        ----------
        node : node()
            A node to walk. The node must be either an XML document node or an XML
            element node; it cannot be a text node.
        expr : item()*
            An expression to evaluate for each match. You can use the variables
            $cts:text , $cts:node , $cts:entity-type , $cts:normalized-text ,
            $cts:entity-id , $cts:start , and $cts:action in the expression. See the
            Usage Notes for details.
        dict : cts:entity-dictionary
            The entity dictionary to use for matching entities in the text of the input
            node. If you omit this parameter, the default entity dictionary is used. (No
            default dictionaries currently exist.) See the Usage Notes for details.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-walk``.

        Notes
        -----
        The following variables are available for use inline in the expr parameter.
        These variables make aspects of the matched entity available to your inline
        code. $cts:node as text() The node containing the match. $cts:text as xs:string
        The matched text. In the case of overlapping matches, this value may not
        encompass the entirety of the entity match string. Rather, it contains only the
        non-overlapping part of the text, in order to prevent introduction of duplicate
        text in the final result. $cts:entity-type The type of the matched entity, as
        defined by the type field of the matching entity dictionary entry.
        $cts:entity-id The ID of the matched entity, as defined by the id field of the
        matching entity dictionary entry. $cts:normalized-text as xs:string The
        normalized entity text (only applicable to some languages). $cts:start as
        xs:integer The offset (in codepoints) of the start of $cts:text in the matched
        text node. $cts:action as xs:string The action to take. Use xdmp:set on this
        variable in your inline code to specify what should happen next. Use xdmp:set to
        set the value to one of the following: "continue" Walk the next match. If there
        are no more matches, return all evaluation results. This is the default action.
        "skip" Skip walking any more matches and return all evaluation results. "break"
        Stop walking matches and return all evaluation results.

        Native reference: https://docs.marklogic.com/cts:entity-walk
        """
        return _FunctionCall(
            "cts:entity-walk",
            (node, expr),
            (dict,),
        )

    @staticmethod
    def estimate(
        query=None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        maximum=None,
    ) -> Expr:
        """Build a composable ``cts:estimate`` call.

        Returns the number of fragments selected by a search.

        Parameters
        ----------
        query : cts:query?
            Query to estimate. None supplies the required empty query slot.
        options : (cts:order|xs:string)*
            Options to this search. The default is (). See cts.search for details on
            available options.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            (). In the XQuery version, you can use cts:search with this parameter and an
            empty cts:and-query to specify a forest-specific XPath statement (see the
            third example below). If you use this to constrain an XPath to one or more
            forests, you should set the quality-weight to zero to keep the XPath
            document order.
        maximum : xs:double?
            The maximum value to return. Stop selecting fragments if this number is
            reached.

        Returns
        -------
        Expr
            Composable call to ``cts:estimate``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:estimate
        """
        return _FunctionCall(
            "cts:estimate",
            (query,),
            (options, _double(quality_weight), forest_ids, _double(maximum)),
        )

    @staticmethod
    def false_query() -> Expr:
        """Build a composable ``cts:false-query`` call.

        Returns a query that matches no fragments.

        Returns
        -------
        Expr
            Composable call to ``cts:false-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:false-query
        """
        return _FunctionCall(
            "cts:false-query",
            (),
        )

    @staticmethod
    def field_range_query(
        field_name,
        operator,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:field-range-query`` call.

        Returns a cts:query matching fields by name with a range-index entry
        equal to a given value.

        Parameters
        ----------
        field_name : xs:string*
            One or more field names to match. When multiple field names are specified,
            the query matches if any field name matches.
        operator : xs:string
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : xs:anyAtomicType*
            One or more field values to match. When multiple values are specified, the
            query matches if any value matches. The value must be a type for which there
            is a range index defined.
        options : xs:string*
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:field-range-query``.

        Notes
        -----
        If you want to constrain on a range of values, you can combine multiple
        cts:field-range-query constructors together with cts:and-query or any of the
        other composable cts:query constructors.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        The "cached-incremental" option can improve performance if you repeatedly
        perform range queries on date or dateTime values over a short range that does
        not vary widely over short period of time. To benefit, the operator should
        remain the same "direction" (<,<=, or >,>=) across calls, the bounding date or
        dateTime changes slightly across calls, and the query runs very frequently
        (multiple times per minute). Note that using this options creates significantly
        more cached queries than the "cached" option.

        The "cached-incremental" option has the following restrictions and interactions:
        The "min-occurs" and "max-occurs" options will be ignored if you use
        "cached-incremental" in unfiltered search. You can only use
        "score-function=zero" with "cached-incremental". The "cached-incremental" option
        behaves like "cached" if you are not querying date or dateTime values.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        For queries against a dateTime index, when $value is an xs:dayTimeDuration or
        xs:yearMonthDuration, the query is executed as an age query. $value is
        subtracted from fn:current-dateTime() to create an xs:dateTime used in the
        query. If there is more than one item in $value, they must all be the same type.

        Native reference: https://docs.marklogic.com/cts:field-range-query
        """
        return _FunctionCall(
            "cts:field-range-query",
            (field_name, _operator(operator), value),
            (options, _double(weight)),
        )

    @staticmethod
    def field_reference(field, *, options=None) -> Expr:
        """Build a composable ``cts:field-reference`` call.

        Creates a reference to a field value lexicon, for use as a parameter to
        cts:value-tuples.

        Parameters
        ----------
        field : xs:string
            A field name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (int, unsignedInt, long, unsignedLong,
            float, double, decimal, dateTime, time, date, gYearMonth, gYear, gMonth,
            gDay, yearMonthDuration, dayTimeDuration, string, anyURI, point, or
            long-lat-point) "collation= URI " Use the lexicon with the collation
            specified by URI . "nullable" Allow null values in tuples reported from
            cts:value-tuples when using this lexicon. "unchecked" Read the scalar type,
            collation and coordinate-system info only from the input. Do not check the
            definition against the context database. "coordinate-system= name " Create a
            reference to an index or lexicon based on the specified coordinate system.
            Allowed values: "wgs84", "wgs84/double", "raw", "raw/double". Only
            applicable if the index/lexicon value type is point or long-lat-point .
            "precision= value " Create a reference to an index or lexicon configured
            with the specified geospatial precision. Allowed values: float and double .
            Only applicable if the index/lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.

        Returns
        -------
        Expr
            Composable call to ``cts:field-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:field-reference
        """
        return _FunctionCall(
            "cts:field-reference",
            (field,),
            (options,),
        )

    @staticmethod
    def field_value_co_occurrences(
        field_name_1,
        field_name_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:field-value-co-occurrences`` call.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified field value lexicon(s).

        Parameters
        ----------
        field_name_1 : xs:string
            A string.
        field_name_2 : xs:string
            A string.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-co-occurrences``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the co-occurrences returned by this function,
        use fn:subsequence on the output, rather than the "skip" option. The "skip"
        option is based on fragments matching the query parameter (if present), not on
        values. A fragment matched by query might contain multiple occurrences or no
        occurrences. The number of fragments skipped does not correspond to the number
        of values. Also, the skip is applied to the relevance ordered query matches, not
        to the ordered co-occurrences list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:field-value-co-occurrences
        """
        return _FunctionCall(
            "cts:field-value-co-occurrences",
            (field_name_1, field_name_2),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def field_value_match(
        field_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:field-value-match`` call.

        Returns values from the specified field value lexicon(s) that match the
        specified wildcard pattern.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a range index with that collation does not exist, an error
        is thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Native reference: https://docs.marklogic.com/cts:field-value-match
        """
        return _FunctionCall(
            "cts:field-value-match",
            (field_names, pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def field_value_query(field_name, text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:field-value-query`` call.

        Returns a query matching text content containing a given value in the
        specified field.

        Parameters
        ----------
        field_name : xs:string*
            One or more field names to search over. If multiple field names are
            supplied, the match can be in any of the specified fields (or-query
            semantics).
        text : xs:anyAtomicType*
            The values to match. If multiple values are specified, the query matches if
            any of the values match (or-query semantics). For XML and metadata, the
            values should be strings. For JSON, the values can be strings, numbers or
            booleans to match correspondingly typed nodes. To match null, pass in the
            empty sequence.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple or score-random (because those scoring algorithms do
            not consider term frequency, proximity is irrelevant). "min-occurs= number "
            Specifies the minimum number of occurrences required. If fewer that this
            number of words occur, the fragment does not match. The default is 1.
            "max-occurs= number " Specifies the maximum number of occurrences required.
            If more than this number of words occur, the fragment does not match. The
            default is unbounded. "synonym" Specifies that all of the terms in the $text
            parameter are considered synonyms for scoring purposes. The result is that
            occurrences of more than one of the synonyms are scored as if there are more
            occurrences of the same term (as opposed to having a separate term that
            contributes to score). "lexicon-expansion-limit= number " Specifies the
            limit for lexicon expansion. This puts a restriction on the number of
            lexicon expansions that can be performed. If the limit is exceeded, the
            server may raise an error depending on whether the "limit-check" option is
            set. The default value for this option will be 4096. "limit-check" Specifies
            that an error will be raised if the lexicon expansion exceeds the specified
            limit. "no-limit-check" Specifies that error will not be raised if the
            lexicon expansion exceeds the specified limit. The server will try to
            resolve the wildcard.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-query``.

        Notes
        -----
        If you use cts:near-query with cts:field-value-query , the distance supplied in
        the near query applies to the whole document, not just to the field. For
        example, if you specify a near query with a distance of 3, it will return
        matches when the values are within 3 words in the whole document, For a code
        example illustrating this, see the second example below.

        Values are determined based on words (tokens)of values of elements that are
        included in the field. Field values span all the included elements. They cannot
        span excluded elements (this is because MarkLogic Server breaks out of the field
        when it encounters the excluded element and start it again field when it
        encounters the next included element). Field values will also span included
        sibling elements.

        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        When you use the "exact" option, you should also enable "fast case sensitive
        searches" and "fast diacritic sensitive searches" in your database
        configuration.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Native reference: https://docs.marklogic.com/cts:field-value-query
        """
        return _FunctionCall(
            "cts:field-value-query",
            (field_name, text),
            (options, _double(weight)),
        )

    @staticmethod
    def field_value_ranges(
        field_names,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:field-value-ranges`` call.

        Returns value ranges from the specified field value lexicon(s).

        Parameters
        ----------
        field_names : xs:string*
            One or more element QNames.
        bounds : xs:anyAtomicType*
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-ranges``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then ranges with all
        included values may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        results list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:field-value-ranges
        """
        return _FunctionCall(
            "cts:field-value-ranges",
            (field_names,),
            (bounds, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def field_values(
        field_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:field-values`` call.

        Returns values from the specified field value lexicon(s).

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        start : xs:anyAtomicType?
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:field-values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:field-values
        """
        return _FunctionCall(
            "cts:field-values",
            (field_names,),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def field_word_match(
        field_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:field-word-match`` call.

        Returns words from the specified field word lexicon(s) that match a
        wildcard pattern.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:field-word-match``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Only words that can be matched with field-word-query are included. That is, only
        words present in immediate text node children of the specified field as well as
        any text node children of child fields defined in the Admin Interface as
        field-word-query-throughs or phrase-throughs.

        Native reference: https://docs.marklogic.com/cts:field-word-match
        """
        return _FunctionCall(
            "cts:field-word-match",
            (field_names, pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def field_word_query(field_name, text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:field-word-query`` call.

        Returns a query matching fields with text content containing a given
        phrase.

        Parameters
        ----------
        field_name : xs:string*
            One or more field names to search over. If multiple field names are
            supplied, the match can be in any of the specified fields (or-query
            semantics).
        text : xs:string*
            The word or phrase to match. If multiple strings are specified, the query
            matches if any of the words or phrases match (or-query semantics).
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:field-word-query``.

        Notes
        -----
        If you use cts:near-query with cts:field-word-query , the distance supplied in
        the near query applies to the whole document, not just to the field. For
        example, if you specify a near query with a distance of 3, it will return
        matches when the words or phrases are within 3 words in the whole document, even
        if some of those words are not in the specified field. For a code example
        illustrating this, see the second example below.

        Phrases are determined based on words being next to each other (word positions
        with a distance of 1) and words being in the same instance of the field. Because
        field word positions are determined based on the fragment, not on the field,
        field phrases cannot span excluded elements (this is because MarkLogic Server
        breaks out of the field when it encounters the excluded element and start a new
        field when it encounters the next included element). Similarly, field phrases
        will not span included sibling elements. The second code example below
        illustrates this.

        The phrase-through feature will be enabled once you include the path element in
        the field setting. Field phrases will automatically phrase-through all child
        elements of an included element, until it encounters an explicitly excluded
        element. The third example below illustrates this. An example of when this
        automatic phrase-through behavior might be convenient is if you create a field
        that includes only the element ABSTRACT . Then all child elements of ABSTRACT
        are included in the field, and phrases would span all of the child elements
        (that is, phrases would "phrase-through" all the child elements).

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Native reference: https://docs.marklogic.com/cts:field-word-query
        """
        return _FunctionCall(
            "cts:field-word-query",
            (field_name, text),
            (options, _double(weight)),
        )

    @staticmethod
    def field_words(
        field_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:field-words`` call.

        Returns words from the specified field word lexicon.

        Parameters
        ----------
        field_names : xs:string*
            One or more field names.
        start : xs:string?
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:field-words``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        Only words that can be matched with field-word-query are included. That is, only
        words present in immediate text node children of the specified field as well as
        any text node children of child fields defined in the Admin Interface as
        field-word-query-throughs or phrase-throughs.

        When run without a $query parameter and as a user with the admin role, the word
        lexicon functions return results that might include words from deleted
        fragments. However, when run as a user with the admin role and without a $query
        parameter, the word lexicon functions run faster (because they do not need to
        look up where each word comes from). It is therefore faster to run word lexicon
        functions as an admin user without passing a $query parameter.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:field-words
        """
        return _FunctionCall(
            "cts:field-words",
            (field_names,),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def fitness(*, node=None) -> Expr:
        """Build a composable ``cts:fitness`` call.

        Returns the fitness of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : node()
            A node. Typically this is an item in the result sequence of a cts:search
            operation.

        Returns
        -------
        Expr
            Composable call to ``cts:fitness``.

        Notes
        -----
        Fitness is similar to score, except that it is bounded. It is similar to
        confidence, except that it is not influenced by term IDFs. It is an xs:float in
        the range of 0.0 to 1.0. It does not include quality.

        Native reference: https://docs.marklogic.com/cts:fitness
        """
        return _FunctionCall(
            "cts:fitness",
            (),
            (node,),
        )

    @staticmethod
    def fitness_order(*, options=None) -> Expr:
        """Build a composable ``cts:fitness-order`` call.

        Creates a fitness-based ordering clause, for use as an option to
        cts:search.

        Parameters
        ----------
        options : xs:string*
            Options. Options include: "descending" Return results in descending order of
            fitness. "ascending" Return results in ascending order of fitness.

        Returns
        -------
        Expr
            Composable call to ``cts:fitness-order``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Native reference: https://docs.marklogic.com/cts:fitness-order
        """
        return _FunctionCall(
            "cts:fitness-order",
            (),
            (options,),
        )

    @staticmethod
    def frequency(value) -> Expr:
        """Build a composable ``cts:frequency`` call.

        Returns an integer representing the number of times in which a
        particular value occurs in a value lexicon lookup.

        Parameters
        ----------
        value : item()
            A value from a lexicon lookup function. For example, a value returned by a
            function such as cts:values , cts:words , cts:field-values ,
            cts:field-word-match , or cts:geospatial-boxes .

        Returns
        -------
        Expr
            Composable call to ``cts:frequency``.

        Notes
        -----
        You must have a suitable index configured to use the lexicon APIs. For example
        you must configure a range index to use value lexicon lookup functions such as
        cts:element-values , cts:element-value-match , cts:element-attribute-values , or
        cts:element-attribute-value-match .

        If the value specified is not from a value lexicon lookup, this function returns
        a frequency of 0.

        When using the fragment-frequency lexicon option, this function returns the
        number of fragments in which the lexicon value occurs. When using the
        item-frequency lexicon option, this function returns the total number of times
        in which the lexicon value occurs in each item.

        The frequency returned this function is fragment-based by default (using the
        default fragment-frequency option in the lexicon API). If there are multiple
        occurrences of the value in any given fragment, the frequency is still one per
        fragment when using fragment-frequency . For example, if this function returns a
        value of 13, then the input value occurs in 13 fragments.

        To get the total frequency rather than the fragment-based frequency, pass the
        item-frequency option to the lexicon lookup function that generates the input
        values for this function. See the second example, below.

        Native reference: https://docs.marklogic.com/cts:frequency
        """
        return _FunctionCall(
            "cts:frequency",
            (value,),
        )

    @staticmethod
    def geospatial_attribute_pair_reference(
        element,
        lat,
        long,
        *,
        options=None,
    ) -> Expr:
        """Build a composable ``cts:geospatial-attribute-pair-reference`` call.

        Creates a reference to a geospatial attribute pair range index, for use
        as a parameter to cts:value-tuples This function will throw an exception
        if the specified range index does not exist.

        Parameters
        ----------
        element : xs:QName
            An element QName name.
        lat : xs:QName
            An attribute QName name.
        long : xs:QName
            An attribute QName name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-attribute-pair-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-attribute-pair-reference
        """
        return _FunctionCall(
            "cts:geospatial-attribute-pair-reference",
            (_qname(element), _qname(lat), _qname(long)),
            (options,),
        )

    @staticmethod
    def geospatial_boxes(
        geo_indexes,
        *,
        latitude_bounds=None,
        longitude_bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:geospatial-boxes`` call.

        Returns boxes derived from the specified point lexicon(s).

        Parameters
        ----------
        geo_indexes : cts:reference*
            A sequence of references to geospatial indexes.
        latitude_bounds : xs:double*
            A sequence of latitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        longitude_bounds : xs:double*
            A sequence of longitude bounds. The values must be in strictly ascending
            order, otherwise an exception is thrown.
        options : xs:string*
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
        query : cts:query?
            Only include points in fragments selected by this query, and compute
            frequencies from this set of included points. The points do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-boxes``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If "sample= N " is not specfied in the options parameter, then all boxes with
        included points may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then points from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple boxes or no boxes. The
        number of fragments skipped does not correspond to the number of boxes. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        box list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:geospatial-boxes
        """
        return _FunctionCall(
            "cts:geospatial-boxes",
            (geo_indexes,),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def geospatial_co_occurrences(
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
    ) -> Expr:
        """Build a composable ``cts:geospatial-co-occurrences`` call.

        Find value co-occurrences from two geospatial lexicons.

        Parameters
        ----------
        geo_element_name_1 : xs:QName
            A QName identifying the first lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the child-1-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in child-1-name-1 and child-1-name-2 .
        child_1_name_1 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-1 that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name-1 identifies an element or JSON property
            geospatial lexicon.
        child_1_name_2 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-1 that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        geo_element_name_2 : xs:QName
            A QName identifying the first lexicon. This must reference a geospatial
            lexicon. If it is an element child or JSON property child geospatial
            lexicon, pass the child QName in the child-2-name-1 parameter. For an
            element, element attribute, or JSON property child pair geospatial lexicon,
            pass the child QNames in child-2-name-1 and child-2-name-2 .
        child_2_name_1 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-2 that holds either the lat and longitude
            coordinates (element child geospatial lexicon) or the latitude coordinate
            (element/attribute/JSON property child pair geospatial lexicon). Use an
            empty sequence if geo-element-name-2 identifies an element or JSON property
            geospatial lexicon.
        child_2_name_2 : xs:QName?
            An element, element attribute QName or JSON property name identifying the
            child of geo-element-name-2 that holds the longitude coordinate when working
            with an element/attribute/JSON property child pair geospatial lexicon. Use
            empty sequence for an element or JSON property geospatial lexicon or element
            or JSON property child geospatial lexicon.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by this query, and compute
            frequencies from this set of included co-occurrences. The co-occurrences do
            not need to match the query, but they must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-co-occurrences``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the default coordinate system is used. If a lexicon with that coordinate system
        does not exist, an error is thrown.

        If "sample= N " is not specfied in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specfied in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by the query might produce multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        value list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:geospatial-co-occurrences
        """
        return _FunctionCall(
            "cts:geospatial-co-occurrences",
            (
                _qname(geo_element_name_1),
                _qname(child_1_name_1),
                _qname(child_1_name_2),
                _qname(geo_element_name_2),
            ),
            (
                _qname(child_2_name_1) if child_2_name_1 is not None else None,
                _qname(child_2_name_2) if child_2_name_2 is not None else None,
                options,
                query,
                _double(quality_weight),
                forest_ids,
            ),
        )

    @staticmethod
    def geospatial_element_child_reference(element, child, *, options=None) -> Expr:
        """Build a composable ``cts:geospatial-element-child-reference`` call.

        Creates a reference to a geospatial element child range index, for use
        as a parameter to cts:value-tuples.

        Parameters
        ----------
        element : xs:QName
            An element QName name.
        child : xs:QName
            An element QName name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-element-child-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-element-child-reference
        """
        return _FunctionCall(
            "cts:geospatial-element-child-reference",
            (_qname(element), _qname(child)),
            (options,),
        )

    @staticmethod
    def geospatial_element_pair_reference(element, lat, long, *, options=None) -> Expr:
        """Build a composable ``cts:geospatial-element-pair-reference`` call.

        Creates a reference to a geospatial element pair range index, for use as
        a parameter to cts:value-tuples.

        Parameters
        ----------
        element : xs:QName
            An element QName name.
        lat : xs:QName
            An element QName name.
        long : xs:QName
            An element QName name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-element-pair-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-element-pair-reference
        """
        return _FunctionCall(
            "cts:geospatial-element-pair-reference",
            (_qname(element), _qname(lat), _qname(long)),
            (options,),
        )

    @staticmethod
    def geospatial_element_reference(element, *, options=None) -> Expr:
        """Build a composable ``cts:geospatial-element-reference`` call.

        Creates a reference to a geospatial element range index, for use as a
        parameter to cts:value-tuples.

        Parameters
        ----------
        element : xs:QName
            An element name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-element-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference: https://docs.marklogic.com/cts:geospatial-element-reference
        """
        return _FunctionCall(
            "cts:geospatial-element-reference",
            (_qname(element),),
            (options,),
        )

    @staticmethod
    def geospatial_json_property_child_reference(
        property,
        child,
        *,
        options=None,
    ) -> Expr:
        """Build a composable ``cts:geospatial-json-property-child-reference`` call.

        Creates a reference to a geospatial json property child range index, for
        use as a parameter to cts:value-tuples cts:value-tuples.

        Parameters
        ----------
        property : xs:string
            A JSON property name.
        child : xs:string
            A JSON property name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-json-property-child-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-json-property-child-reference
        """
        return _FunctionCall(
            "cts:geospatial-json-property-child-reference",
            (property, child),
            (options,),
        )

    @staticmethod
    def geospatial_json_property_pair_reference(
        property,
        lat,
        long,
        *,
        options=None,
    ) -> Expr:
        """Build a composable ``cts:geospatial-json-property-pair-reference`` call.

        Creates a reference to a geospatial JSON property pair range index, for
        use as a parameter to cts:value-tuples.

        Parameters
        ----------
        property : xs:string
            A JSON property name.
        lat : xs:string
            A JSON property name.
        long : xs:string
            A JSON property name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= name " Use the given coordinate system. Possible values
            Allowed values: "wgs84", "wgs84/double", "etrs89", "etrs89/double", "raw",
            "raw/double". "precision= value " Use the coordinate system at the given
            precision. Allowed values: float and double . "nullable" Allow null values
            in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-json-property-pair-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-json-property-pair-reference
        """
        return _FunctionCall(
            "cts:geospatial-json-property-pair-reference",
            (property, lat, long),
            (options,),
        )

    @staticmethod
    def geospatial_json_property_reference(property, *, options=None) -> Expr:
        """Build a composable ``cts:geospatial-json-property-reference`` call.

        Creates a reference to a geospatial json property range index, for use
        as a parameter to cts:value-tuples.

        Parameters
        ----------
        property : xs:string
            A JSON property name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples . when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-json-property-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-json-property-reference
        """
        return _FunctionCall(
            "cts:geospatial-json-property-reference",
            (property,),
            (options,),
        )

    @staticmethod
    def geospatial_path_reference(path_expression, *, options=None, map=None) -> Expr:
        """Build a composable ``cts:geospatial-path-reference`` call.

        Creates a reference to a geospatial path range index, for use as a
        parameter to cts:value-tuples.

        Parameters
        ----------
        path_expression : xs:string
            A path expression.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (point or long-lat-point)
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "nullable" Allow null
            values in tuples reported from cts:value-tuples when using this lexicon.
            "unchecked" Read the scalar type and coordinate-system info only from the
            input. Do not check the definition against the context database.
        map : map:map
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the interpretation of the path.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-path-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference: https://docs.marklogic.com/cts:geospatial-path-reference
        """
        bindings = namespace_map(map)
        return _FunctionCall(
            "cts:geospatial-path-reference",
            (index_path(path_expression, bindings),),
            (options, bindings),
        )

    @staticmethod
    def geospatial_region_path_reference(
        path_expression,
        *,
        options=None,
        namespaces=None,
        geohash_precision=None,
        units=None,
        invalid_values=None,
    ) -> Expr:
        """Build a composable ``cts:geospatial-region-path-reference`` call.

        Create a reference to a geospatial region path index, for use as a
        parameter to cts:geospatial-region-query and other query operations on
        geospatial region indexes.

        Parameters
        ----------
        path_expression : xs:string
            The XPath expression specified in the index configuration.
        options : xs:string*
            Index configuration options. The default is (). These options should match
            the configuration used when creating the index. Available options:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "unchecked"
            Read the coordinate-system info only from the input. Do not check the
            definition against the context database.
        namespaces : map:map
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the interpretation of the path.
        geohash_precision : xs:integer?
            The geohash precision specified in the index configuration. Values between 1
            and 12 inclusive are possible.
        units : xs:string?
            The units specified in the index configuration. 'miles', 'km', 'feet', and
            'meters' are valid.
        invalid_values : xs:string?
            The invalid values setting specified in the index configuration. 'reject'
            and 'ignore' are valid.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-region-path-reference``.

        Notes
        -----
        precision

        coordinate-system

        precision

        Native reference:
        https://docs.marklogic.com/cts:geospatial-region-path-reference
        """
        namespaces = namespace_map(namespaces)
        return _FunctionCall(
            "cts:geospatial-region-path-reference",
            (index_path(path_expression, namespaces),),
            (options, namespaces, geohash_precision, units, invalid_values),
        )

    @staticmethod
    def geospatial_region_query(
        geospatial_region_reference,
        operation,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:geospatial-region-query`` call.

        Construct a query to match regions in documents that satisfy a specified
        relationship relative to other regions.

        Parameters
        ----------
        geospatial_region_reference : cts:reference*
            Zero or more geospatial path region index references that identify regions
            in your content. To create a reference, see
            cts:geospatial-region-path-reference .
        operation : xs:string
            The match operation to apply between the regions specified in the
            $geospatial-region-reference parameter and the regions in the $regions
            parameter. Allowed values: contains , covered-by , covers , disjoint ,
            intersects , overlaps , within , equals , touches , crosses . See the Usage
            Notes for details.
        regions : cts:region*
            Criteria regions to match against the regions specified in the
            $geospatial-region-reference parameter. These regions function as the right
            operand of $operation .
        options : xs:string*
            Options to this query. The default is (). Available options: "units= value "
            Measure distances and the radii of circles using the given units. Allowed
            values: miles (default), km , feet , and meters . This option only affects
            regions provided in the $regions parameter, not regions stored in documents.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score). "tolerance= distance " Tolerance is the
            largest allowable variation in geometry calculations. If the distance
            between two points is less than tolerance, then the two points are
            considered equal. For the raw coordinate system, use the units of the
            coordinates. For geographic coordinate systems, use the units specified by
            the units option.
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-region-query``.

        Notes
        -----
        This function matches regions in documents in the database satisfying the
        relationship R1 op R2 , where R1 is a region in a database document, op is the
        operator provided in the operation parameter, and R2 is any of the regions
        provided in the regions parameter. The R1 regions under considerations are those
        in the indexes provided in the geospatial-region-reference parameter.

        The database configuration must include a geospatial path region index
        corresponding to each R1 region. For details, see Geospatial Region Queries and
        Indexes in the Search Developer's Guide .

        The operations are defined by the Dimensionally Extended nine-Intersection Model
        (DE-9IM) of spatial relations. They have the following semantics:

        "contains" R1 contains R2 if every point of R2 is also a point of R1 , and their
        interiors intersect. "covered-by" R1 is covered-by R2 if every point of R1 is
        also a point of R2 . "covers" R1 covers R2 if every point of R2 is also a point
        of R1 . "disjoint" R1 is disjoint from R2 if they have no points in common.
        "intersects" R1 intersects R2 if the two regions have at least one point in
        common. "overlaps" R1 overlaps R2 if the two regions partially intersect -- that
        is, they have some but not all points in common -- and the intersection of R1
        and R2 has the same dimension as R1 and R2 . "within" R1 is within R2 if every
        point of R1 is also a point of R2 , and their interiors intersect. "equals" R1
        equals R2 if every point of R1 is a point of R2 , and every point of R2 is a
        point of R1 . That is, the regions are topologically equal. "touches" R1 touches
        R2 if they have a boundary point in common but no interior points in common.
        "crosses" R1 crosses R2 if their interiors intersect and the dimension of the
        intersection is less than that of at least one of the regions.

        Note: the operation covers differs from contains only in that covers does not
        distinguish between points in the boundary and the interior of geometries. In
        general, covers should be used in preference to contains . Similarly, covered-by
        should generally be used in preference to within .

        If either the geospatial-region-reference or regions parameter is an empty list,
        the query will not match any documents.

        The query uses the coordinate system and precision of the geospatial region
        index reference supplied in the geospatial-region-reference parameter. If
        multiple index references are specified and they have conflicting coordinate
        systems, an XDMP-INCONSCOORD error is thrown.

        Native reference: https://docs.marklogic.com/cts:geospatial-region-query
        """
        return _FunctionCall(
            "cts:geospatial-region-query",
            (geospatial_region_reference, operation, regions),
            (options, _double(weight)),
        )

    @staticmethod
    def highlight(node, query, expr) -> Expr:
        """Build a composable ``cts:highlight`` call.

        Returns a copy of the node, replacing any text matching the query with
        the specified expression.

        Parameters
        ----------
        node : node()
            A node to highlight. The node must be either a document node or an element
            node; it cannot be a text node.
        query : cts:query
            A query specifying the text to highlight. If a string is entered, the string
            is treated as a cts:word-query of the specified string.
        expr : item()*
            An expression with which to replace each match. You can use the variables
            $cts:text , $cts:node , $cts:queries , $cts:start , and $cts:action
            (described below) in the expression.

        Returns
        -------
        Expr
            Composable call to ``cts:highlight``.

        Notes
        -----
        There are five built-in variables to represent a query match. These variables
        can be used inline in the expression parameter.

        $cts:text as xs:string The matched text. $cts:node as text() The node containing
        the matched text. $cts:queries as cts:query* The matching queries. $cts:start as
        xs:integer The string-length position of the first character of $cts:text in
        $cts:node . Therefore, the following always returns true:
        fn:substring($cts:node, $cts:start, fn:string-length($cts:text)) eq $cts:text
        $cts:action as xs:string Use xdmp:set on this to specify what should happen next
        "continue" (default) Walk the next match. If there are no more matches, return
        all evaluation results. "skip" Skip walking any more matches and return all
        evaluation results. "break" Stop walking matches and return all evaluation
        results.

        You cannot use cts:highlight to highlight results matching cts:similar-query and
        cts:element-attribute-*-query items. Using cts:highlight with these queries will
        return the nodes without any highlighting.

        You can also use cts:highlight as a general search and replace function. The
        specified expression will replace any matching text. For example, you could
        replace the word "hello" with "goodbye" in a query similar to the following:

        cts:highlight($node, "hello", "goodbye")

        Because the expressions can be any XQuery expression, they can be very simple
        like the above example or they can be extremely complex.

        Unfiltered queries, including registered queries, do not match in cts:walk or
        cts:highlight .

        Native reference: https://docs.marklogic.com/cts:highlight
        """
        return _FunctionCall(
            "cts:highlight",
            (node, query, expr),
        )

    @staticmethod
    def index_order(index, *, options=None) -> Expr:
        """Build a composable ``cts:index-order`` call.

        Creates a index-based ordering clause, for use as an option to
        cts:search.

        Parameters
        ----------
        index : cts:reference
            A reference to a range index.
        options : xs:string*
            Options. The default is (). Options include: "descending" Results should be
            returned in descending order of index. "ascending" Results should be
            returned in ascending order of index.

        Returns
        -------
        Expr
            Composable call to ``cts:index-order``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Native reference: https://docs.marklogic.com/cts:index-order
        """
        return _FunctionCall(
            "cts:index-order",
            (index,),
            (options,),
        )

    @staticmethod
    def iri_reference() -> Expr:
        """Build a composable ``cts:iri-reference`` call.

        Creates a reference to the URI lexicon, for use as a parameter to
        cts:value-tuples.

        Returns
        -------
        Expr
            Composable call to ``cts:iri-reference``.

        Notes
        -----
        Requires MarkLogic 11 or later. Availability is checked by the server
        when the expression is evaluated, including in nested expressions.

        Native reference: https://docs.marklogic.com/cts:iri-reference
        """
        return _FunctionCall(
            "cts:iri-reference",
            (),
        )

    @staticmethod
    def json_property_child_geospatial_query(
        parent_property_name,
        child_property_names,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-child-geospatial-query`` call.

        Returns a query matching json properties by name which has specific
        children representing latitude and longitude values for a point
        contained within the given geographic box, circle, or polygon, or equal
        to the given point.

        Parameters
        ----------
        parent_property_name : xs:string*
            One or more parent property names to match. When multiple names are
            specified, the query matches if any name matches.
        child_property_names : xs:string*
            One or more child property names to match. When multiple names are
            specified, the query matches if any name matches; however, only the first
            matching latitude child in any point instance will be checked. The property
            must specify both latitude and longitude coordinates.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= string " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "units= value
            " Measure distance and the radii of circles in the specified units. Allowed
            values: miles (default), km , feet , meters . "boundaries-included" Points
            on boxes', circles', and polygons' boundaries are counted as matching. This
            is the default. "boundaries-excluded" Points on boxes', circles', and
            polygons' boundaries are not counted as matching.
            "boundaries-latitude-excluded" Points on boxes' latitude boundaries are not
            counted as matching. "boundaries-longitude-excluded" Points on boxes'
            longitude boundaries are not counted as matching.
            "boundaries-south-excluded" Points on the boxes' southern boundaries are not
            counted as matching. "boundaries-west-excluded" Points on the boxes' western
            boundaries are not counted as matching. "boundaries-north-excluded" Points
            on the boxes' northern boundaries are not counted as matching.
            "boundaries-east-excluded" Points on the boxes' eastern boundaries are not
            counted as matching. "boundaries-circle-excluded" Points on circles'
            boundary are not counted as matching. "boundaries-endpoints-excluded" Points
            on linestrings' boundary (the endpoints) are not counted as matching.
            "cached" Cache the results of this query in the list cache. "uncached" Do
            not cache the results of this query in the list cache. "type=long-lat-point"
            Specifies the format for the point in the data as longitude first, latitude
            second. "type=point" Specifies the format for the point in the data as
            latitude first, longitude second. This is the default format.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-child-geospatial-query``.

        Notes
        -----
        The point value is expressed in the content of the property as a child of
        numbers, separated by whitespace and punctuation (excluding decimal points and
        sign characters).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Point values and boundary specifications of boxes are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference:
        https://docs.marklogic.com/cts:json-property-child-geospatial-query
        """
        return _FunctionCall(
            "cts:json-property-child-geospatial-query",
            (parent_property_name, child_property_names, regions),
            (options, _double(weight)),
        )

    @staticmethod
    def json_property_geospatial_query(
        property_name,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-geospatial-query`` call.

        Returns a query matching json properties by name whose content
        represents a point contained within the given geographic box, circle, or
        polygon, or equal to the given point.

        Parameters
        ----------
        property_name : xs:string*
            One or more json property names to match. When multiple names are specified,
            the query matches if any name matches.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= string " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "units= value
            " Measure distance and the radii of circles in the specified units. Allowed
            values: miles (default), km , feet , meters . "boundaries-included" Points
            on boxes', circles', and polygons' boundaries are counted as matching. This
            is the default. "boundaries-excluded" Points on boxes', circles', and
            polygons' boundaries are not counted as matching.
            "boundaries-latitude-excluded" Points on boxes' latitude boundaries are not
            counted as matching. "boundaries-longitude-excluded" Points on boxes'
            longitude boundaries are not counted as matching.
            "boundaries-south-excluded" Points on the boxes' southern boundaries are not
            counted as matching. "boundaries-west-excluded" Points on the boxes' western
            boundaries are not counted as matching. "boundaries-north-excluded" Points
            on the boxes' northern boundaries are not counted as matching.
            "boundaries-east-excluded" Points on the boxes' eastern boundaries are not
            counted as matching. "boundaries-circle-excluded" Points on circles'
            boundary are not counted as matching. "boundaries-endpoints-excluded" Points
            on linestrings' boundary (the endpoints) are not counted as matching.
            "cached" Cache the results of this query in the list cache. "uncached" Do
            not cache the results of this query in the list cache. "type=long-lat-point"
            Specifies the format for the point in the data as longitude first, latitude
            second. "type=point" Specifies the format for the point in the data as
            latitude first, longitude second. This is the default format.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-geospatial-query``.

        Notes
        -----
        The point value is expressed in the content of the element as a pair of numbers,
        separated by whitespace and punctuation (excluding decimal points and sign
        characters).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Point values and boundary specifications of boxes are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:json-property-geospatial-query
        """
        return _FunctionCall(
            "cts:json-property-geospatial-query",
            (property_name, regions),
            (options, _double(weight)),
        )

    @staticmethod
    def json_property_pair_geospatial_query(
        property_name,
        latitude_property_names,
        longitude_property_names,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-pair-geospatial-query`` call.

        Returns a query matching json properties by name which has specific
        property children representing latitude and longitude values for a point
        contained within the given geographic box, circle, or polygon, or equal
        to the given point.

        Parameters
        ----------
        property_name : xs:string*
            One or more parent property names to match. When multiple names are
            specified, the query matches if any name matches.
        latitude_property_names : xs:string*
            One or more latitude property names to match. When multiple names are
            specified, the query matches if any name matches; however, only the first
            matching latitude child in any point instance will be checked.
        longitude_property_names : xs:string*
            One or more longitude property names to match. When multiple names are
            specified, the query matches if any name matches; however, only the first
            matching longitude child in any point instance will be checked.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-pair-geospatial-query``.

        Notes
        -----
        Point values and boundary specifications of boxes are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference:
        https://docs.marklogic.com/cts:json-property-pair-geospatial-query
        """
        return _FunctionCall(
            "cts:json-property-pair-geospatial-query",
            (property_name, latitude_property_names, longitude_property_names, regions),
            (options, _double(weight)),
        )

    @staticmethod
    def json_property_range_query(
        property_name,
        operator,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-range-query`` call.

        Returns a cts:query matching JSON properties by name with a range-index
        entry equal to a given value.

        Parameters
        ----------
        property_name : xs:string*
            One or more property name to match. When multiple names are specified, the
            query matches if any name matches.
        operator : xs:string
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : xs:anyAtomicType*
            One or more property values to match. When multiple values are specified,
            the query matches if any value matches. The value must be a type for which
            there is a range index defined.
        options : xs:string*
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-range-query``.

        Notes
        -----
        If you want to constrain on a range of values, you can combine multiple
        cts:json-property-range-query constructors together with cts:and-query or any of
        the other composable cts:query constructors.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        The "cached-incremental" option can improve performance if you repeatedly
        perform range queries on date or dateTime values over a short range that does
        not vary widely over short period of time. To benefit, the operator should
        remain the same "direction" (<,<=, or >,>=) across calls, the bounding date or
        dateTime changes slightly across calls, and the query runs very frequently
        (multiple times per minute). Note that using this options creates significantly
        more cached queries than the "cached" option.

        The "cached-incremental" option has the following restrictions and interactions:
        The "min-occurs" and "max-occurs" options will be ignored if you use
        "cached-incremental" in unfiltered search. You can only use
        "score-function=zero" with "cached-incremental". The "cached-incremental" option
        behaves like "cached" if you are not querying date or dateTime values.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        For queries against a dateTime index, when $value is an xs:dayTimeDuration or
        xs:yearMonthDuration, the query is executed as an age query. $value is
        subtracted from fn:current-dateTime() to create an xs:dateTime used in the
        query. If there is more than one item in $value, they must all be the same type.

        Native reference: https://docs.marklogic.com/cts:json-property-range-query
        """
        return _FunctionCall(
            "cts:json-property-range-query",
            (property_name, _operator(operator), value),
            (options, _double(weight)),
        )

    @staticmethod
    def json_property_reference(property, *, options=None) -> Expr:
        """Build a composable ``cts:json-property-reference`` call.

        Creates a reference to a JSON property value lexicon, for use as a
        parameter to cts:value-tuples.

        Parameters
        ----------
        property : xs:string
            A property name.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (int, unsignedInt, long, unsignedLong,
            float, double, decimal, dateTime, time, date, gYearMonth, gYear, gMonth,
            gDay, yearMonthDuration, dayTimeDuration, string, anyURI, point, or
            long-lat-point) "collation= URI " Use the lexicon with the collation
            specified by URI . "nullable" Allow null values in tuples reported from
            cts:value-tuples when using this lexicon. "unchecked" Read the scalar type,
            collation and coordinate-system info only from the input. Do not check the
            definition against the context database. "coordinate-system= name " Create a
            reference to an index or lexicon based on the specified coordinate system.
            Allowed values: "wgs84", "wgs84/double", "raw", "raw/double". Only
            applicable if the index/lexicon value type is point or long-lat-point .
            "precision= value " Create a reference to an index or lexicon configured
            with the specified geospatial precision. Allowed values: float and double .
            Only applicable if the index/lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:json-property-reference
        """
        return _FunctionCall(
            "cts:json-property-reference",
            (property,),
            (options,),
        )

    @staticmethod
    def json_property_scope_query(property_name, query) -> Expr:
        """Build a composable ``cts:json-property-scope-query`` call.

        Returns a cts:query matching JSON properties by name with the content
        constrained by the given cts:query in the second parameter.

        Parameters
        ----------
        property_name : xs:string*
            One or more property names to match. When multiple names are specified, the
            query matches if any name matches.
        query : cts:query
            A query for the property to match. If a string is entered, the string is
            treated as a cts:word-query of the specified string.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-scope-query``.

        Notes
        -----
        cts:json-property-scope-query

        Native reference: https://docs.marklogic.com/cts:json-property-scope-query
        """
        return _FunctionCall(
            "cts:json-property-scope-query",
            (property_name, query),
        )

    @staticmethod
    def json_property_value_query(
        property_name,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-value-query`` call.

        Returns a query matching JSON properties by name with value equal the
        given value.

        Parameters
        ----------
        property_name : xs:string*
            One or more property names to match. When multiple names are specified, the
            query matches if any name matches.
        value : xs:anyAtomicType*
            One or more property values to match. When multiple values are specified,
            the query matches if any value matches. The values can be strings, numbers
            or booleans to match correspondingly typed nodes. If the value is the empty
            sequence, the query matches null.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-value-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        When you use the "exact" option, you should also enable "fast case sensitive
        searches" and "fast diacritic sensitive searches" in your database
        configuration.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Note that the text content for the value in a cts:json-property-value-query is
        treated the same as a phrase in a cts:word-query , where the phrase is the
        property value. Therefore, any wildcard and/or stemming rules are treated like a
        phrase. For example, if you have an property value of "hello friend" with
        wildcarding enabled for a query, a cts:json-property-value-query for "he*" will
        not match because the wildcard matches do not span word boundaries, but a
        cts:json-property-value-query for "hello *" will match. A search for "*" will
        match, because a "*" wildcard by itself is defined to match the value.
        Similarly, stemming rules are applied to each term, so a search for "hello
        friends" would match when stemming is enabled for the query because "friends"
        matches "friend". For an example, see the fourth example below.

        Similarly, because a "*" wildcard by itself is defined to match the value, the
        following query will match any property with the name my-property , regardless
        of the wildcard indexes enabled in the database configuration:
        cts:json-property-value-query("my-property", "*", "wildcarded")

        Native reference: https://docs.marklogic.com/cts:json-property-value-query
        """
        return _FunctionCall(
            "cts:json-property-value-query",
            (property_name, value),
            (options, _double(weight)),
        )

    @staticmethod
    def json_property_word_match(
        property_names,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-word-match`` call.

        Returns words from the specified JSON property word lexicon(s) that
        match a wildcard pattern.

        Parameters
        ----------
        property_names : xs:string*
            One or more property names.
        pattern : xs:string?
            Wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-word-match``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Only words that can be matched with json-property-word-query are included.

        Native reference: https://docs.marklogic.com/cts:json-property-word-match
        """
        return _FunctionCall(
            "cts:json-property-word-match",
            (property_names, pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def json_property_word_query(
        property_name,
        text,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-word-query`` call.

        Returns a query matching JSON properties by name with text content
        containing a given phrase.

        Parameters
        ----------
        property_name : xs:string*
            One or more JSON property names to match. When multiple names are specified,
            the query matches if any name matches.
        text : xs:string*
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard. "no-limit-check" is default, if neither "limit-check" nor
            "no-limit-check" is explicitly specified.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-word-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Relevance adjustment for the "distance-weight" option depends on the closest
        proximity of any two matches of the query. For example,
        cts:json-property-word-query(xs:QName("p"),("dog","cat"),("distance-weight=10"))
        will adjust relevance based on the distance between the closest pair of matches
        of either "dog" or "cat" within a property named "p" (the pair may consist only
        of matches of "dog", only of matches of "cat", or a match of "dog" and a match
        of "cat").

        Native reference: https://docs.marklogic.com/cts:json-property-word-query
        """
        return _FunctionCall(
            "cts:json-property-word-query",
            (property_name, text),
            (options, _double(weight)),
        )

    @staticmethod
    def json_property_words(
        property_names,
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:json-property-words`` call.

        Returns words from the specified JSON property word lexicon.

        Parameters
        ----------
        property_names : xs:string*
            One or more property names.
        start : xs:string?
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-words``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        Only words that can be matched with json-property-word-query are included.

        When run without a $query parameter and as a user with the admin role, the word
        lexicon functions return results that might include words from deleted
        fragments. However, when run as a user with the admin role and without a $query
        parameter, the word lexicon functions run faster (because they do not need to
        look up where each word comes from). It is therefore faster to run word lexicon
        functions as an admin user without passing a $query parameter.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:json-property-words
        """
        return _FunctionCall(
            "cts:json-property-words",
            (property_names,),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def linear_model(values, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:linear-model`` call.

        Returns a linear model that fits the frequency-weighted data set.

        Parameters
        ----------
        values : cts:reference*
            References to two range indexes. The types of the range indexes must be
            numeric. If the size of this sequence is not 2, the function returns the
            empty sequence.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:linear-model``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:linear-model
        """
        return _FunctionCall(
            "cts:linear-model",
            (values,),
            (options, query, forest_ids),
        )

    @staticmethod
    def linestring(vertices) -> Expr:
        """Build a composable ``cts:linestring`` call.

        Returns a geospatial linestring value.

        Parameters
        ----------
        vertices : (cts:point*|xs:string)
            The waypoints of the linestring, given in order. Alternatively, the vertices
            may be provided as a string that follows the well-known text (WKT) scheme
            for a linestring.

        Returns
        -------
        Expr
            Composable call to ``cts:linestring``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:linestring
        """
        return _FunctionCall(
            "cts:linestring",
            (vertices,),
        )

    @staticmethod
    def locks_fragment_query(query) -> Expr:
        """Build a composable ``cts:locks-fragment-query`` call.

        Returns a query that matches all documents where $query matches
        document-locks.

        Parameters
        ----------
        query : cts:query
            A query to be matched against the locks fragment.

        Returns
        -------
        Expr
            Composable call to ``cts:locks-fragment-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:locks-fragment-query
        """
        return _FunctionCall(
            "cts:locks-fragment-query",
            (query,),
        )

    @staticmethod
    def lsqt_query(
        temporal_collection,
        *,
        timestamp=None,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:lsqt-query`` call.

        Returns only documents before LSQT or a timestamp before LSQT for stable
        query results.

        Parameters
        ----------
        temporal_collection : xs:string
            The name of the temporal collection.
        timestamp : xs:dateTime?
            Return only temporal documents with a system start time less than or equal
            to this value. Default is temporal:get-lsqt($temporal-collection) .
            Timestamps larger than LSQT are rejected.
        options : xs:string*
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "cached-incremental" Break down the
            query into sub-queries and then cache each one of them for better
            performance. This is enabled, by default. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:lsqt-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:lsqt-query
        """
        return _FunctionCall(
            "cts:lsqt-query",
            (temporal_collection,),
            (timestamp, options, _double(weight)),
        )

    @staticmethod
    def match_regions(
        range_indexes,
        operation,
        regions,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:match-regions`` call.

        Find regions in documents that have a spatial relationship to one or
        more caller-supplied regions.

        Parameters
        ----------
        range_indexes : cts:reference*
            References to range indexes that store the string serialization of regions
            to match against.
        operation : xs:string
            The operation to test. Must be one of the following: contains , covered-by ,
            covers , crosses , disjoint , equals , intersects , overlaps , touches ,
            within . See the Usage Notes for details.
        regions : cts:region*
            One or more cts:region values to test against. A region matches if it
            matches against any of these regions.
        options : xs:string*
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
        query : cts:query?
            Limit the region comparison to documents that match this query. Also,
            compute frequencies from the set of included regions. The values do not need
            to match the query, but they must occur in fragments selected by the query.
            The fragments are not filtered to ensure they match the query. Instead, they
            are selected in the same manner as "unfiltered" cts:search operations.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search should be constrained. An
            empty sequence means search all forests in the database. The default is an
            empty sequence.

        Returns
        -------
        Expr
            Composable call to ``cts:match-regions``.

        Notes
        -----
        This function matches regions in documents in the database satisfying the
        relationship R1 op R2 , where R1 is a region in a database document, op is the
        operator provided in the operation parameter, and R2 is any of the regions
        provided in the regions parameter. The R1 regions under considerations are those
        in the indexes provided in the range-indexes parameter. The R1 regions can be
        further constrained to those in documents that match a query.

        The operations are defined by the Dimensionally Extended nine-Intersection Model
        (DE-9IM) of spatial relations. They have the following semantics:

        "contains" R1 contains R2 if every point of R2 is also a point of R1 , and their
        interiors intersect. "covered-by" R1 is covered-by R2 if every point of R1 is
        also a point of R2 . "covers" R1 covers R2 if every point of R2 is also a point
        of R1 . "crosses" R1 crosses R2 if their interiors intersect and the dimension
        of the intersection is less than that of at least one of the regions. "disjoint"
        R1 is disjoint from R2 if they have no points in common. "equals" R1 equals R2
        if every point of R1 is a point of R2 , and every point of R2 is a point of R1 .
        That is, the regions are topologically equal. "intersects" R1 intersects R2 if
        the two regions have at least one point in common. "overlaps" R1 overlaps R2 if
        the two regions partially intersect -- that is, they have some but not all
        points in common -- and the intersection of R1 and R2 has the same dimension as
        R1 and R2 . "touches" R1 touches R2 if they have a boundary point in common but
        no interior points in common. "within" R1 is within R2 if every point of R1 is
        also a point of R2 , and their interiors intersect.

        Note: the operation covers differs from contains only in that covers does not
        distinguish between points in the boundary and the interior of geometries. In
        general, covers should be used in preference to contains . Similarly, covered-by
        should generally be used in preference to within .

        The return value is either a sequence of cts:region values or a sequence of
        strings containing the serialized regions, depending on whether or not the
        strings option is included.

        If the range indexes provided through the range-indexes parameter contain any
        string that cannot be parsed into a region, an error is thrown.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "coordinate-system= name " is not specified in the options parameter, then
        the governing coordinate system is used.

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the operation uses single precision.

        Native reference: https://docs.marklogic.com/cts:match-regions
        """
        return _FunctionCall(
            "cts:match-regions",
            (range_indexes, operation, regions),
            (options, query, forest_ids),
        )

    @staticmethod
    def max(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:max`` call.

        Returns the maximal value given a value lexicon.

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

        Returns
        -------
        Expr
            Composable call to ``cts:max``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:max
        """
        return _FunctionCall(
            "cts:max",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def median(arg) -> Expr:
        """Build a composable ``cts:median`` call.

        Returns a frequency-weighted median of a sequence.

        Parameters
        ----------
        arg : xs:double*
            The sequence of values. The values should be the result of a lexicon lookup.

        Returns
        -------
        Expr
            Composable call to ``cts:median``.

        Notes
        -----
        This function is designed to take a sequence of values returned by a lexicon
        function (for example, cts:element-values ); if you input non-lexicon values,
        the result will be the empty sequence.

        Native reference: https://docs.marklogic.com/cts:median
        """
        return _FunctionCall(
            "cts:median",
            (arg,),
        )

    @staticmethod
    def min(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:min`` call.

        Returns the minimal value given a value lexicon.

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

        Returns
        -------
        Expr
            Composable call to ``cts:min``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:min
        """
        return _FunctionCall(
            "cts:min",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def near_query(
        queries,
        *,
        distance=None,
        options=None,
        distance_weight=None,
    ) -> Expr:
        """Build a composable ``cts:near-query`` call.

        Returns a query matching all of the specified queries, where the matches
        occur within the specified distance from each other.

        Parameters
        ----------
        queries : cts:query*
            A sequence of queries to match.
        distance : xs:double?
            A distance, in number of words, between any two matching queries. The
            results match if two queries match and the distance between the two matches
            is equal to or less than the specified distance. A distance of 0 matches
            when the text is the exact same text or when there is overlapping text (see
            the third example below). A negative distance is treated as 0. The default
            value is 10.
        options : xs:string*
            Options to this query. The default value is (). Options include: "ordered"
            Any near-query matches must occur in the order of the specified sub-queries.
            "unordered" Any near-query matches will satisfy the query, regardless of the
            order they were specified. "minimum-distance" The minimum distance between
            two matching queries. The results match if the two queries match and the
            minimum distance between the two matches is greater than or equal to the
            specified minimum distance. The default value is zero. A negative distance
            is treated as 0.
        distance_weight : xs:double?
            A weight attributed to the distance for this query. Higher weights add to
            the importance of distance (as opposed to term matches) when the relevance
            order is calculated. The default value is 1.0. The weight should be between
            64 and -16. Weights greater than 64 will have the same effect as a weight of
            64. Weights less than the absolute value of 0.0625 (between -0.0625 and
            0.0625) are rounded to 0, which means that they do not contribute to the
            score. This parameter has no effect if the word positions index is not
            enabled.

        Returns
        -------
        Expr
            Composable call to ``cts:near-query``.

        Notes
        -----
        If the options parameter contains neither "ordered" nor "unordered", then the
        default is "unordered".

        The word positions index will speed the performance of queries that use
        cts:near-query . The element word positions index will speed the performance of
        element-queries that use cts:near-query .

        If you use cts:near-query with a field, the distance specified is the distance
        in the whole document, not the distance in the field. For example, if the
        distance between two words is 20 in the document, but the distance is 10 if you
        look at a view of the document that only includes the elements in a field, a
        cts:near-query must have a distance of 20 or more to match; a distance of 10
        would not match. The same applies to minimum distance as well.

        If you use cts:near-query with cts:field-word-query , the distance supplied in
        the near query applies to the whole document, not just to the field. This too
        applies to the minimum distance as well. For details, see cts:field-word-query .

        Expressions using the ordered option are more efficient than those using the
        unordered option, especially if they specify many queries to match.

        Minimum-distance and distances apply to each near-query match. Therefore, if
        minimum-distance is greater than distance there can be no matches.

        Native reference: https://docs.marklogic.com/cts:near-query
        """
        return _FunctionCall(
            "cts:near-query",
            (queries,),
            (_double(distance), options, _double(distance_weight)),
        )

    @staticmethod
    def not_in_query(positive_query, negative_query) -> Expr:
        """Build a composable ``cts:not-in-query`` call.

        Returns a query matching the first sub-query, where those matches do not
        occur within 0 distance of the other query.

        Parameters
        ----------
        positive_query : cts:query
            A positive query, specifying the search results filtered in.
        negative_query : cts:query
            A negative query, specifying the search results to filter out.

        Returns
        -------
        Expr
            Composable call to ``cts:not-in-query``.

        Notes
        -----
        Positions are required to accurately resolve this query from the indexes. If you
        do not enable position indexes appropriate to the type of the sub-queries, then
        you may get surprising results in unfiltered searches. For example, if the sub
        queries are cts:word-query , then you should enable word positions in the
        database.

        False positives can occur if there are no positions available, such as when
        positions are not enabled. Filtered searches always have access to positions,
        but unfiltered searches do not.

        Some query types are intrinsically positionless, such as cts:collection-query or
        cts:directory-query . Matches to such a query are considered to occur at every
        position and causes the overall query to behave like cst:and-not-query . If no
        position can be determined, such as when positions are not enabled, then every
        match to $positive-query is a match for the whole query.

        Native reference: https://docs.marklogic.com/cts:not-in-query
        """
        return _FunctionCall(
            "cts:not-in-query",
            (positive_query, negative_query),
        )

    @staticmethod
    def not_query(query) -> Expr:
        """Build a composable ``cts:not-query`` call.

        Returns a query specifying the matches not specified by its sub-query.

        Parameters
        ----------
        query : cts:query
            A negative query, specifying the search results to filter out.

        Returns
        -------
        Expr
            Composable call to ``cts:not-query``.

        Notes
        -----
        cts:not-query

        cts:not-query

        $query

        cts:not-query

        cts:search

        $query

        cts:not-query

        Native reference: https://docs.marklogic.com/cts:not-query
        """
        return _FunctionCall(
            "cts:not-query",
            (query,),
        )

    @staticmethod
    def or_query(queries, *, options=None) -> Expr:
        """Build a composable ``cts:or-query`` call.

        Returns a query specifying the union of the matches specified by the
        sub-queries.

        Parameters
        ----------
        queries : cts:query*
            A sequence of sub-queries.
        options : xs:string*
            Options to this query. The default is () . Options include: "synonym"
            Specifies that all of the terms in the $queries parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).

        Returns
        -------
        Expr
            Composable call to ``cts:or-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:or-query
        """
        return _FunctionCall(
            "cts:or-query",
            (queries,),
            (options,),
        )

    @staticmethod
    def parse(query, *, bindings=None) -> Expr:
        """Build a composable ``cts:parse`` call.

        Parses a query string

        Parameters
        ----------
        query : xs:string
            The query string. For details, see Creating a Query From Search Text With
            cts:parse in the Search Developer's Guide .
        bindings : map:map?
            Bindings for mapping x:y parts of the query string. The map key can be
            either a simple string with no embedded spaces or punctuation or the empty
            string. The empty string defines the parsing of untagged words. For details,
            see Binding a Tag to a Reference, Field, or Query Generator in the Search
            Developer's Guide . The map value for the label can be: cts:reference A
            reference to the tag in the query corresponds to a query against the
            indicated index, which constructs a query. Reference Operator Query
            cts:element-reference ":" cts:element-word-query cts:element-reference "="
            cts:element-value-query cts:element-attribute-reference ":"
            cts:element-attribute-word-query cts:element-attribute-reference "="
            cts:element-attribute-value-query cts:json-property-reference ":"
            cts:json-property-word-query cts:json-property-reference "="
            cts:json-property-value-query cts:field-reference ":" cts:field-word-query
            cts:field-reference "=" cts:field-value-query geospatial reference ":"
            geospatial query, parameter parsed as a region geospatial reference "=" or
            eq geospatial query, parameter parsed as a region geospatial reference other
            operator error cts:uri-reference ":" cts:document-query cts:uri-reference
            "=" cts:document-query cts:collection-reference ":" cts:collection-query
            cts:collection-reference "=" cts:collection-query cts:path-reference ":"
            cts:word-query (no path word-query) cts:path-reference "="
            cts:path-range-query with operator "=" (no path value-query) any EQ
            range-query with operator "=" any NE range-query with operator "!=" any LT
            range-query with operator "<" any LE range-query with operator "<=" any GE
            range-query with operator ">=" any GT range-query with operator ">" function
            ($operator as xs:string, $values as xs:string*, $options as xs:string*) as
            cts:query? A reference to the tag in the query calls the function to produce
            a query. xs:string A reference to the tag in the query corresponds to a
            field query against the named field.

        Returns
        -------
        Expr
            Composable call to ``cts:parse``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:parse
        """
        return _FunctionCall(
            "cts:parse",
            (query,),
            (bindings,),
        )

    @staticmethod
    def part_of_speech(token) -> Expr:
        """Build a composable ``cts:part-of-speech`` call.

        Returns the part of speech for a cts:token, if any.

        Parameters
        ----------
        token : cts:token
            A token, as returned from cts:tokenize .

        Returns
        -------
        Expr
            Composable call to ``cts:part-of-speech``.

        Notes
        -----
        This function is useful for testing custom tokenizers. Built in tokenizers do
        not use parts of speech and will return an empty string for the part of speech.

        Native reference: https://docs.marklogic.com/cts:part-of-speech
        """
        return _FunctionCall(
            "cts:part-of-speech",
            (token,),
        )

    @staticmethod
    def path_geospatial_query(
        path_expression,
        regions,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:path-geospatial-query`` call.

        Returns a query matching path expressions whose content represents a
        point contained within the given geographic box, circle, or polygon, or
        equal to the given point.

        Parameters
        ----------
        path_expression : xs:string*
            One or more path expressions to match. When multiple path expressions are
            specified, the query matches if any path expression matches.
        regions : cts:region*
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : xs:string*
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "type=long-lat-point" Specifies the format for the point
            in the data as longitude first, latitude second. "type=point" Specifies the
            format for the point in the data as latitude first, longitude second. This
            is the default format. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:path-geospatial-query``.

        Notes
        -----
        The point value is expressed in the content of an element that matches given
        path expression as a pair of numbers, separated by whitespace and punctuation
        (excluding decimal points and sign characters).

        The value of the precision option takes precedence over that implied by the
        governing coordinate system name, including the value of the coordinate-system
        option. For example, if the governing coordinate system is "wgs84/double" and
        the precision option is "float", then the query uses single precision.

        Point values and boundary specifications of boxes are given in degrees relative
        to the WGS84 coordinate system. Southern latitudes and Western longitudes take
        negative values. Longitudes will be wrapped to the range (-180,+180) and
        latitudes will be clipped to the range (-90,+90).

        If the northern boundary of a box is south of the southern boundary, no points
        will match. However, longitudes wrap around the globe, so that if the western
        boundary is east of the eastern boundary, then the box crosses the
        anti-meridian.

        Special handling occurs at the poles, as all longitudes exist at latitudes +90
        and -90.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:path-geospatial-query
        """
        return _FunctionCall(
            "cts:path-geospatial-query",
            (index_path(path_expression), regions),
            (options, _double(weight)),
        )

    @staticmethod
    def path_range_query(
        path_expression,
        operator,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:path-range-query`` call.

        Returns a cts:query matching documents where the content addressed by an
        XPath expression satisfies the specified relationship (=, <, >, etc.)
        with respect to the input criteria values.

        Parameters
        ----------
        path_expression : xs:string*
            One or more XPath expressions that identify the content to match. When
            multiple paths are specified, the query matches if any path matches.
        operator : xs:string
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : xs:anyAtomicType*
            One or more values to match. These values are compared to the value(s)
            addressed by the path-expression parameter. When multiple When multiple
            values are specified, the query matches if any value matches. The value must
            be a type for which there is a range index defined.
        options : xs:string*
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:path-range-query``.

        Notes
        -----
        If you want to constrain on a range of values, you can combine multiple
        cts:path-range-query constructors together with cts:and-query or any of the
        other composable cts:query constructors.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        The "cached-incremental" option can improve performance if you repeatedly
        perform range queries on date or dateTime values over a short range that does
        not vary widely over short period of time. To benefit, the operator should
        remain the same "direction" (<,<=, or >,>=) across calls, the bounding date or
        dateTime changes slightly across calls, and the query runs very frequently
        (multiple times per minute). Note that using this options creates significantly
        more cached queries than the "cached" option.

        The "cached-incremental" option has the following restrictions and interactions:
        The "min-occurs" and "max-occurs" options will be ignored if you use
        "cached-incremental" in unfiltered search. You can only use
        "score-function=zero" with "cached-incremental". The "cached-incremental" option
        behaves like "cached" if you are not querying date or dateTime values.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        For queries against a dateTime index, when $value is an xs:dayTimeDuration or
        xs:yearMonthDuration, the query is executed as an age query. $value is
        subtracted from fn:current-dateTime() to create an xs:dateTime used in the
        query. If there is more than one item in $value, they must all be the same type.

        Native reference: https://docs.marklogic.com/cts:path-range-query
        """
        return _FunctionCall(
            "cts:path-range-query",
            (index_path(path_expression), _operator(operator), value),
            (options, _double(weight)),
        )

    @staticmethod
    def path_reference(path_expression, *, options=None, namespaces=None) -> Expr:
        """Build a composable ``cts:path-reference`` call.

        Creates a reference to a path value lexicon, for use as a parameter to
        cts:value-tuples.

        Parameters
        ----------
        path_expression : xs:string
            A path range index expression.
        options : xs:string*
            Options. The default is (). Options include: "type= type " Use the lexicon
            with the type specified by type (int, unsignedInt, long, unsignedLong,
            float, double, decimal, dateTime, time, date, gYearMonth, gYear, gMonth,
            gDay, yearMonthDuration, dayTimeDuration, string, anyURI, point, or
            long-lat-point) "collation= URI " Use the lexicon with the collation
            specified by URI . "nullable" Allow null values in tuples reported from
            cts:value-tuples when using this lexicon. "unchecked" Read the scalar type,
            collation and coordinate-system info only from the input. Do not check the
            definition against the context database. "coordinate-system= name " Create a
            reference to an index or lexicon based on the specified coordinate system.
            Allowed values: "wgs84", "wgs84/double", "raw", "raw/double". Only
            applicable if the index/lexicon value type is point or long-lat-point .
            "precision= value " Create a reference to an index or lexicon configured
            with the specified geospatial precision. Allowed values: float and double .
            Only applicable if the index/lexicon value type is point or long-lat-point .
            This value takes precedence over the precision implicit in the coordinate
            system name.
        namespaces : map:map
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the interpretation of the path.

        Returns
        -------
        Expr
            Composable call to ``cts:path-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:path-reference
        """
        namespaces = namespace_map(namespaces)
        return _FunctionCall(
            "cts:path-reference",
            (index_path(path_expression, namespaces),),
            (options, namespaces),
        )

    @staticmethod
    def percent_rank(arg, value, *, options=None) -> Expr:
        """Build a composable ``cts:percent-rank`` call.

        Returns the rank of a value in a data set as a percentage of the data
        set.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values.
        value : xs:anyAtomicType
            The value to be "ranked".
        options : xs:string*
            Options. The default is (). Options include: "ascending"(default) Rank the
            value as if the sequence was sorted in ascending order. "descending" Rank
            the value as if the sequence was sorted in descending order. "collation= URI
            " Applies only when $arg is of the xs:string type. If no specified, the
            default collation is used. "coordinate-system= name " Applies only when $arg
            is of the cts:point type. If no specified, the default coordinate system is
            used.

        Returns
        -------
        Expr
            Composable call to ``cts:percent-rank``.

        Notes
        -----
        This function is designed to take a sequence of values returned by a lexicon
        function (for example, cts:element-values ); if you input non-lexicon values,
        the result will be the empty sequence.

        Native reference: https://docs.marklogic.com/cts:percent-rank
        """
        return _FunctionCall(
            "cts:percent-rank",
            (arg, value),
            (options,),
        )

    @staticmethod
    def percentile(arg, p) -> Expr:
        """Build a composable ``cts:percentile`` call.

        Returns a sequence of percentile(s) given a sequence of percentage(s).

        Parameters
        ----------
        arg : xs:double*
            The sequence of values. The values should be the result of a lexicon lookup.
        p : xs:double*
            The sequence of percentage(s).

        Returns
        -------
        Expr
            Composable call to ``cts:percentile``.

        Notes
        -----
        This function is designed to take a sequence of values returned by a lexicon
        function (for example, cts:element-values ); if you input non-lexicon values,
        the result will be the empty sequence.

        Native reference: https://docs.marklogic.com/cts:percentile
        """
        return _FunctionCall(
            "cts:percentile",
            (arg, p),
        )

    @staticmethod
    def period(start, end) -> Expr:
        """Build a composable ``cts:period`` call.

        Creates a period value, for use as a parameter to cts:period-range-query
        or cts:period-compare-query.

        Parameters
        ----------
        start : xs:dateTime
            The dateTime value indicating start of the period.
        end : xs:dateTime
            The dateTime value indicating end of the period.

        Returns
        -------
        Expr
            Composable call to ``cts:period``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:period
        """
        return _FunctionCall(
            "cts:period",
            (start, end),
        )

    @staticmethod
    def period_compare(period_1, operator, period_2) -> Expr:
        """Build a composable ``cts:period-compare`` call.

        Compares two periods using the specified comparison operator.

        Parameters
        ----------
        period_1 : cts:period
            The first period to compare.
        operator : xs:string
            A comparison operator.
        period_2 : cts:period
            The second period to compare against the first.

        Returns
        -------
        Expr
            Composable call to ``cts:period-compare``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:period-compare
        """
        return _FunctionCall(
            "cts:period-compare",
            (period_1, operator, period_2),
        )

    @staticmethod
    def period_compare_query(axis_1, operator, axis_2, *, options=None) -> Expr:
        """Build a composable ``cts:period-compare-query`` call.

        Returns a cts:query matching documents that have relevant pair of period
        values.

        Parameters
        ----------
        axis_1 : xs:string
            Name of the first axis to compare
        operator : xs:string
            A comparison operator. Period is the two timestamps contained in the axis.
            Operators include: "aln_equals" Match documents whose period1 equals
            period2. "aln_contains" Match documents whose period1 contains period2. i.e.
            period1 starts before period2 starts and ends before period2 ends.
            "aln_contained_by" Match documents whose period1 is contained by period2.
            "aln_meets" Match documents whose period1 meets period2, i.e. period1 ends
            at period2 start. "aln_met_by" Match documents whose period1 meets period2,
            i.e. period1 starts at period2 end. "aln_before" Match documents whose
            period1 is before period2, i.e. period1 ends before period2 starts.
            "aln_after" Match documents whose period1 is after period2, i.e. period1
            starts after period2 ends. "aln_starts" Match documents whose period1 starts
            period2, i.e. period1 starts at period2 start and ends before period2 ends.
            "aln_started_by" Match documents whose period2 starts period1, i.e. period1
            starts at period2 start and ends after period2 ends. "aln_finishes" Match
            documents whose period1 finishes period2, i.e. period1 finishes at period2
            finish and starts after period2 starts. "aln_finished_by" Match documents
            whose period2 finishes period1, i.e. period1 finishes at period2 finish and
            starts before period2 starts. "aln_overlaps" Match documents whose period1
            overlaps period2, i.e. period1 starts before period2 start and ends before
            period2 ends but after period2 starts. "aln_overlapped_by" Match documents
            whose period2 overlaps period1, i.e. period1 starts after period2 start but
            before period2 ends and ends after period2 ends. "iso_contains" Match
            documents whose period1 contains period2 in sql 2011 standard. i.e. period1
            starts before or at period2 starts and ends after or at period2 ends.
            "iso_overlaps" Match documents whose period1 overlaps period2 in sql 2011
            standard. i.e. period1 and period2 have common time period. "iso_succeeds"
            Match documents whose period1 succeeds period2 in sql 2011 standard. i.e.
            period1 starts at or after period2 ends "iso_precedes" Match documents whose
            period1 precedes period2 in sql 2011 standard. i.e. period1 ends at or
            before period2 ends "iso_succeeds" Match documents whose period1 succeeds
            period2 in sql 2011 standard. i.e. period1 starts at or after period2 ends
            "iso_precedes" Match documents whose period1 precedes period2 in sql 2011
            standard. i.e. period1 ends at or before period2 ends "iso_imm_succeeds"
            Match documents whose period1 immediately succeeds period2 in sql 2011
            standard. i.e. period1 starts at period2 ends "iso_imm_precedes" Match
            documents whose period1 immediately precedes period2 in sql 2011 standard.
            i.e. period1 ends at period2 ends
        axis_2 : xs:string
            Name of the second period to compare
        options : xs:string*
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache.

        Returns
        -------
        Expr
            Composable call to ``cts:period-compare-query``.

        Notes
        -----
        If you want to constrain on a range of period comparisons, you can combine
        multiple cts: constructors together with cts:and-query or any of the other
        composable cts:query constructors, as in the last part of the example below.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Native reference: https://docs.marklogic.com/cts:period-compare-query
        """
        return _FunctionCall(
            "cts:period-compare-query",
            (axis_1, operator, axis_2),
            (options,),
        )

    @staticmethod
    def period_range_query(axis_name, operator, *, period=None, options=None) -> Expr:
        """Build a composable ``cts:period-range-query`` call.

        Returns a cts:query matching axis by name with a period value with an
        operator.

        Parameters
        ----------
        axis_name : xs:string*
            One or more axis to match on.
        operator : xs:string
            A comparison operator. Operators include: "aln_equals" Match documents whose
            period1 equals value. "aln_contains" Match documents whose period1 contains
            value. i.e. period1 starts before value starts and ends before value ends.
            "aln_contained_by" Match documents whose period1 is contained by value.
            "aln_meets" Match documents whose period1 meets value, i.e. period1 ends at
            value start. "aln_met_by" Match documents whose period1 meets value, i.e.
            period1 starts at value end. "aln_before" Match documents whose period1 is
            before value, i.e. period1 ends before value starts. "aln_after" Match
            documents whose period1 is after value, i.e. period1 starts after value
            ends. "aln_starts" Match documents whose period1 starts value, i.e. period1
            starts at value start and ends before value ends. "aln_started_by" Match
            documents whose value starts period1, i.e. period1 starts at value start and
            ends after value ends. "aln_finishes" Match documents whose period1 finishes
            value, i.e. period1 finishes at value finish and starts after value starts.
            "aln_finished_by" Match documents whose value finishes period1, i.e. period1
            finishes at value finish and starts before value starts. "aln_overlaps"
            Match documents whose period1 overlaps value, i.e. period1 starts before
            value start and ends before value ends but after value starts.
            "aln_overlapped_by" Match documents whose value overlaps period1, i.e.
            period1 starts after value start but before value ends and ends after value
            ends. "iso_contains" Match documents whose period1 contains value in sql
            2011 standard. i.e. period1 starts before or at value starts and ends after
            or at value ends. "iso_overlaps" Match documents whose period1 overlaps
            value in sql 2011 standard. i.e. period1 and value have common time period.
            "iso_succeeds" Match documents whose period1 succeeds value in sql 2011
            standard. i.e. period1 starts at or after value ends "iso_precedes" Match
            documents whose period1 precedes value in sql 2011 standard. i.e. period1
            ends at or before value ends "iso_imm_succeeds" Match documents whose
            period1 immediately succeeds value in sql 2011 standard. i.e. period1 starts
            at value end "iso_imm_precedes" Match documents whose period1 immediately
            precedes value in sql 2011 standard. i.e. period1 ends at value end
        period : cts:period*
            the cts:period to perform operations on. When multiple values are specified,
            the query matches if any value matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "min-occurs= number " Specifies the
            minimum number of occurrences required. If fewer that this number of words
            occur, the fragment does not match. The default is 1. "max-occurs= number "
            Specifies the maximum number of occurrences required. If more than this
            number of words occur, the fragment does not match. The default is
            unbounded. "score-function= function " Use the selected scoring function.
            The score function may be: linear Use a linear function of the difference
            between the specified query value and the matching value in the index to
            calculate a score for this range query. reciprocal Use a reciprocal function
            of the difference between the specified query value and the matching value
            in the index to calculate a score for this range query. zero This range
            query does not contribute to the score. This is the default. "slope-factor=
            number " Apply the given number as a scaling factor to the slope of the
            scoring function. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:period-range-query``.

        Notes
        -----
        If you want to constrain on a range of values, you can combine multiple
        cts:period-range-query constructors together with cts:and-query or any of the
        other composable cts:query constructors, as in the last part of the example
        below.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:period-range-query
        """
        return _FunctionCall(
            "cts:period-range-query",
            (axis_name, operator),
            (period, options),
        )

    @staticmethod
    def point(latitude_or_wkt, longitude=None) -> Expr:
        """Build a composable ``cts:point`` call.

        Returns a point value.

        Parameters
        ----------
        latitude_or_wkt : (xs:float|xs:string)
            The latitude of the point. Alternatively, the vertex may be provided as a
            string that follows the well-known text (WKT) scheme for a point.
        longitude : xs:float
            The longitude of the point. If you supply a WKT string as latitude , this
            parameter must not be supplied.

        Returns
        -------
        Expr
            Composable call to ``cts:point``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:point
        """
        return _FunctionCall(
            "cts:point",
            (latitude_or_wkt,),
            (longitude,),
        )

    @staticmethod
    def polygon(vertices) -> Expr:
        """Build a composable ``cts:polygon`` call.

        Returns a geospatial polygon value.

        Parameters
        ----------
        vertices : (cts:point*|xs:string)
            The vertices of the polygon, given in order. No edge may cover more than 180
            degrees of either latitude or longitude. The polygon as a whole may not
            encompass both poles. These constraints are necessary to ensure an
            unambiguous interpretation of the polygon. There must be at least three
            vertices. The first vertex should be identical to the last vertex to close
            the polygon. Alternatively, the vertices may be provided as a string that
            follows the well-known text (WKT) scheme for a polygon.

        Returns
        -------
        Expr
            Composable call to ``cts:polygon``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:polygon
        """
        return _FunctionCall(
            "cts:polygon",
            (vertices,),
        )

    @staticmethod
    def properties_fragment_query(query) -> Expr:
        """Build a composable ``cts:properties-fragment-query`` call.

        Returns a query that matches all documents where $query matches
        document-properties.

        Parameters
        ----------
        query : cts:query
            A query to be matched against the properties fragment.

        Returns
        -------
        Expr
            Composable call to ``cts:properties-fragment-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:properties-fragment-query
        """
        return _FunctionCall(
            "cts:properties-fragment-query",
            (query,),
        )

    @staticmethod
    def quality(*, node=None) -> Expr:
        """Build a composable ``cts:quality`` call.

        Returns the quality of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : node()
            A node. Typically this is an item in the result sequence of a cts:search
            operation.

        Returns
        -------
        Expr
            Composable call to ``cts:quality``.

        Notes
        -----
        If you run cts:quality on a constructed node, it always returns 0; it is
        primarily intended to run on nodes that are the retrieved from the database (an
        item from a cts:search result or an item from the result of an XPath expression
        that searches through the database).

        Native reference: https://docs.marklogic.com/cts:quality
        """
        return _FunctionCall(
            "cts:quality",
            (),
            (node,),
        )

    @staticmethod
    def quality_order(*, options=None) -> Expr:
        """Build a composable ``cts:quality-order`` call.

        Creates a quality-based ordering clause, for use as an option to
        cts:search.

        Parameters
        ----------
        options : xs:string*
            Options. Options include: "descending" Results should be returned in
            descending order of quality. "ascending" Results should be returned in
            ascending order of quality.

        Returns
        -------
        Expr
            Composable call to ``cts:quality-order``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Native reference: https://docs.marklogic.com/cts:quality-order
        """
        return _FunctionCall(
            "cts:quality-order",
            (),
            (options,),
        )

    @staticmethod
    def query(query) -> Expr:
        """Build a composable ``cts:query`` call.

        Creates a query.

        Parameters
        ----------
        query : node()
            A query.

        Returns
        -------
        Expr
            Composable call to ``cts:query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:query
        """
        return _FunctionCall(
            "cts:query",
            (query,),
        )

    @staticmethod
    def range_query(index, operator, value, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:range-query`` call.

        Returns a cts:query matching specified nodes with a range-index entry
        compared to a given value.

        Parameters
        ----------
        index : cts:reference*
            One or more range index references. When multiple indexes are specified, the
            query matches if any index matches.
        operator : xs:string
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : xs:anyAtomicType*
            One or more values to match. When multiple values are specified, the query
            matches if any value matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "min-occurs= number " Specifies the
            minimum number of occurrences required. If fewer that this number of words
            occur, the fragment does not match. The default is 1. "max-occurs= number "
            Specifies the maximum number of occurrences required. If more than this
            number of words occur, the fragment does not match. The default is
            unbounded. "score-function= function " Use the selected scoring function.
            The score function may be: linear Use a linear function of the difference
            between the specified query value and the matching value in the index to
            calculate a score for this range query. reciprocal Use a reciprocal function
            of the difference between the specified query value and the matching value
            in the index to calculate a score for this range query. zero This range
            query does not contribute to the score. This is the default. "slope-factor=
            number " Apply the given number as a scaling factor to the slope of the
            scoring function. The default is 1.0. "synonym" Specifies that all of the
            terms in the $value parameter are considered synonyms for scoring purposes.
            The result is that occurrences of more than one of the synonyms are scored
            as if there are more occurrences of the same term (as opposed to having a
            separate term that contributes to score).
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:range-query``.

        Notes
        -----
        If you want to constrain on a range of values, you can combine multiple
        cts:range-query constructors together with cts:and-query or any of the other
        composable cts:query constructors, as in the last part of the example below.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:range-query
        """
        return _FunctionCall(
            "cts:range-query",
            (index, _operator(operator), value),
            (options, _double(weight)),
        )

    @staticmethod
    def rank(arg, value, *, options=None) -> Expr:
        """Build a composable ``cts:rank`` call.

        Returns the rank of a value in a data set.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values.
        value : xs:anyAtomicType
            The value to be "ranked".
        options : xs:string*
            Options. The default is (). Options include: "ascending"(default) Rank the
            value as if the sequence was sorted in ascending order. "descending" Rank
            the value as if the sequence was sorted in descending order. "collation= URI
            " Applies only when $arg is of the xs:string type. If no specified, the
            default collation is used. "coordinate-system= name " Applies only when $arg
            is of the cts:point type. If no specified, the default coordinate system is
            used.

        Returns
        -------
        Expr
            Composable call to ``cts:rank``.

        Notes
        -----
        This function is designed to take a sequence of values returned by a lexicon
        function (for example, cts:element-values ); if you input non-lexicon values,
        the result will be the empty sequence.

        Native reference: https://docs.marklogic.com/cts:rank
        """
        return _FunctionCall(
            "cts:rank",
            (arg, value),
            (options,),
        )

    @staticmethod
    def reference_parse(reference) -> Expr:
        """Build a composable ``cts:reference-parse`` call.

        Creates a reference to a value lexicon by parsing its XML or JSON
        representation, for use as a parameter to cts:value-tuples.

        Parameters
        ----------
        reference : node()
            A reference to a range index.

        Returns
        -------
        Expr
            Composable call to ``cts:reference-parse``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:reference-parse
        """
        return _FunctionCall(
            "cts:reference-parse",
            (reference,),
        )

    @staticmethod
    def register(query) -> Expr:
        """Build a composable ``cts:register`` call.

        Register a query for later use.

        Parameters
        ----------
        query : cts:query
            A query to register.

        Returns
        -------
        Expr
            Composable call to ``cts:register``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:register
        """
        return _FunctionCall(
            "cts:register",
            (query,),
        )

    @staticmethod
    def registered_query(ids, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:registered-query`` call.

        Returns a query matching fragments specified by previously registered
        queries (see cts:register).

        Parameters
        ----------
        ids : xs:unsignedLong*
            Some registered query identifiers.
        options : xs:string*
            Options to this query. The default is (). Options include: "filtered" A
            filtered query (the default). Filtered queries eliminate any false-positive
            results and properly resolve cases where there are multiple candidate
            matches within the same fragment, thereby guaranteeing that the results
            fully satisfy the original cts:query item that was registered. This option
            is not currently available. "unfiltered" An unfiltered query. Unfiltered
            registered queries select fragments from the indexes that are candidates to
            satisfy the cts:query . Depending on the original cts:query , the structure
            of the documents in the database, and the configuration of the database,
            unfiltered registered queries may result in false-positive results or in
            incorrect matches when there are multiple candidate matches within the same
            fragment. To avoid these problems, you should only use unfiltered queries on
            top-level XPath expressions (for example, document nodes, collections,
            directories) or on fragment roots. Using unfiltered queries on complex XPath
            expressions or on XPath expressions that traverse below a fragment root can
            result in unexpected results. This option is required in the current
            release.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:registered-query``.

        Notes
        -----
        Searches that use registered queries will generate results with different scores
        than the equivalent searches using non-registered queries. This is because
        registered queries are treated as a single term in relevance calculations.

        If the options parameter does not contain "unfiltered", then an error is
        returned, as the "unfiltered" option is required.

        Registered queries are persisted as a soft state only; they can become
        unregistered through an explicit direction (using cts:deregister ), as a result
        of the cache growing too large, or because of a server restart. Consequently,
        either your XQuery code or your middleware layer should handle the case when an
        XDMP-UNREGISTERED exception occurs (for example, you can wrap your
        cts:registered-query code in a try/catch block or your Java or .NET code can
        catch and handle the exception).

        Unfiltered queries, including registered queries, do not match in cts:walk or
        cts:highlight .

        Native reference: https://docs.marklogic.com/cts:registered-query
        """
        return _FunctionCall(
            "cts:registered-query",
            (ids,),
            (options, _double(weight)),
        )

    @staticmethod
    def relevance_info(*, node=None, output_kind=None) -> Expr:
        """Build a composable ``cts:relevance-info`` call.

        Return the relevance score computation report for a node.

        Parameters
        ----------
        node : node()
            A node. Typically this is an item in the result sequence of a cts:search
            operation. If this parameter is omitted, the context node is used.
        output_kind : xs:string
            The output kind. It can be either "element" or "object". With "element", the
            built-in returns an XML element. With "object", the built-in returns a
            map:map. The default is "element".

        Returns
        -------
        Expr
            Composable call to ``cts:relevance-info``.

        Notes
        -----
        This function returns an XML report that contains details about the score
        computation only if the following conditions are met: The node parameter or
        context node is the result of a cts:search call that included the
        relevance-trace option; and the score is non-zero. For example, you will not get
        a report if you use the score-zero option on your cts:search , if the search
        returns no results, or if node is not the result of cts:search .

        The score computation reflects the scoring method specified in the cts:search
        expression, if any. The score-zero and score-random methods do not generate a
        report.

        Collecting score computation details with which to generate this report is
        costly, so using the relevance-trace option will slow down your search
        significantly.

        Native reference: https://docs.marklogic.com/cts:relevance-info
        """
        return _FunctionCall(
            "cts:relevance-info",
            (),
            (node, output_kind),
        )

    @staticmethod
    def remainder(*, node=None) -> Expr:
        """Build a composable ``cts:remainder`` call.

        Returns an estimated search result size for a node, or of the context
        node if no node is provided.

        Parameters
        ----------
        node : node()
            A node. Typically this is an item in the result sequence of a cts:search
            operation. If you specify the first item from a cts:search expression, then
            cts:remainder will return an estimate of the number of fragments that match
            that expression.

        Returns
        -------
        Expr
            Composable call to ``cts:remainder``.

        Notes
        -----
        This function makes it efficient to estimate the size of a search result and
        execute that search in the same query. If you only need an estimate of the size
        of a search but do not need to run the search, then xdmp:estimate is more
        efficient.

        To return the estimated size of a search with cts:remainder , use the first item
        of a cts:search result sequence as the parameter to cts:remainder . For example,
        the following query returns the estimated number of fragments that contain the
        word "dog":

        cts:remainder(cts:search(collection(), "dog")[1])

        When you put the position predicate on the cts:search result sequence, MarkLogic
        Server will filter all of the false-positive results up to the specified
        position, but not the false-positive results beyond the specified position.
        Because of this, when you increase the position number in the parameter, the
        result from cts:remainder might decrease by a larger number than the increase in
        position number, or it might not decrease at all. For example, if the query
        above returned 10, then the following query might return 9, it might return 10,
        or it might return less than 9, depending on how the results are dispersed
        throughout different fragments:

        cts:remainder(cts:search(collection(), "dog")[2])

        If you run cts:remainder on a constructed node, it always returns 0; it is
        primarily intended to run on nodes that are the retrieved from the database (an
        item from a search result or an item from the result of an XPath expression that
        searches through the database).

        Native reference: https://docs.marklogic.com/cts:remainder
        """
        return _FunctionCall(
            "cts:remainder",
            (),
            (node,),
        )

    @staticmethod
    def reverse_query(nodes, *, weight=None) -> Expr:
        """Build a composable ``cts:reverse-query`` call.

        Construct a query that matches serialized cts queries, based on a set of
        model input nodes.

        Parameters
        ----------
        nodes : node()*
            Model nodes that must be matchable by queries matched by this reverse query.
            See the Usage Notes for more details.
        weight : xs:double?
            A weight for this query. This parameter has no effect because a reverse
            query does not contribute to score. That is, the score is always 0.

        Returns
        -------
        Expr
            Composable call to ``cts:reverse-query``.

        Notes
        -----
        A reverse query matches serialized cts:query nodes. Construct a reverse query
        from nodes that model what that serialized query should match, rather than
        passing in the target query. For example, to match queries for the word "hello",
        specify a node containing the word "hello" as the nodes parameter. See the
        example, below. Reverse queries are useful for creating alerting applications.

        When evaluating a cts:reverse-query on a set of nodes, the cts:similar-query or
        cts:registered-query components of any stored query will match all nodes.

        You can create a node or document containing a serialized cts:query in XQuery by
        wrapping a cts:query constructor in an XML node. For example, the following
        snippet creates an XML element (foo) that contains a serialized word query:
        <foo>{cts:word-query("my search")}</foo>/element()

        A reverse query can match both the XML and JSON representations of a serialized
        query.

        Native reference: https://docs.marklogic.com/cts:reverse-query
        """
        return _FunctionCall(
            "cts:reverse-query",
            (nodes,),
            (_double(weight),),
        )

    @staticmethod
    def score(*, node=None) -> Expr:
        """Build a composable ``cts:score`` call.

        Returns the score of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : node()
            A node. Typically this is an item in the result sequence of a cts:search
            operation.

        Returns
        -------
        Expr
            Composable call to ``cts:score``.

        Notes
        -----
        Score is computed according to the scoring method specified in the cts:search
        expression, if any.

        If you run cts:score on a constructed node, it always returns 0; it is primarily
        intended to run on nodes that are retrieved from the database (an item from a
        search result or an item from the result of an XPath expression that searches
        through the database).

        Native reference: https://docs.marklogic.com/cts:score
        """
        return _FunctionCall(
            "cts:score",
            (),
            (node,),
        )

    @staticmethod
    def score_order(*, options=None) -> Expr:
        """Build a composable ``cts:score-order`` call.

        Creates a score-based ordering clause, for use as an option to
        cts:search.

        Parameters
        ----------
        options : xs:string*
            Options. Options include: "descending" Return results in descending order of
            score. "ascending" Return results in ascending order of score.

        Returns
        -------
        Expr
            Composable call to ``cts:score-order``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Native reference: https://docs.marklogic.com/cts:score-order
        """
        return _FunctionCall(
            "cts:score-order",
            (),
            (options,),
        )

    @staticmethod
    def search(
        expression=None,
        query=None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:search`` call.

        Returns a relevance-ordered sequence of nodes specified by a given
        query.

        Parameters
        ----------
        expression : node()*
            An expression to be searched. This must be an inline fully searchable path
            expression. Python strings are wrapped internally and validated
            with the other literal paths in the expression before execution.
        query : cts:query?
            A cts:query specifying the search to perform. If a string is entered, the
            string is treated as a cts:word-query of the specified string.
        options : (cts:order|xs:string)*
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
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            (). In the XQuery version, you can use cts:search with this parameter and an
            empty cts:and-query to specify a forest-specific XPath statement (see the
            third example below). If you use this to constrain an XPath to one or more
            forests, you should set the quality-weight to zero to keep the XPath
            document order.

        Returns
        -------
        Expr
            Composable call to ``cts:search``.

        Notes
        -----
        Queries that use cts:search require that the XPath expression searched is fully
        searchable. A fully searchable path is one that has no steps that are
        unsearchable and whose last step is searchable. You can use the
        xdmp:query-trace() function to see if the path is fully searchable. If there are
        no entries in the xdmp:query-trace() output indicating that a step is
        unsearchable, and if the last step is searchable, then that path is fully
        searchable. Queries that use cts:search on unsearchable XPath expressions will
        fail with an error message. You can often make the path expressions fully
        searchable by rewriting the query or adding new indexes.

        Each node that cts:search returns has a score with which it is associated. To
        access the score, use the cts:score function. The nodes are returned in
        relevance order (most relevant to least relevant), where more relevant nodes
        have a higher score.

        Only one of the "filtered" or "unfiltered" options may be specified in the
        options parameter. If neither "filtered" nor "unfiltered", is specified then the
        default is "filtered".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        "score-zero", or "score-bm25" options may be specified in the options parameter.
        If none of "score-logtfidf", "score-logtf", "score-simple", "score-random",
        "score-zero", or "score-bm25" are specified, then the default is
        "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If the neither "checked" nor "unchecked" are specified, then the
        default is "checked".

        Only one of the "faceted" or "unfaceted" options may be specified in the options
        parameter. If the neither "faceted" nor "unfaceted" are specified, then the
        default is "unfaceted".

        If the cts:query specified is the empty string (equivalent to cts:word-query("")
        ), then the search returns the empty sequence.

        With the cts:index-order parameter, results with no comparable index value are
        always returned at the end of the ordered result sequence.

        With an XQuery "order by" clause, results with no comparable value are normally
        returned by MarkLogic at the end of the ordered result sequence. You can
        override this behavior by specifying the "empty greatest" or "empty least"
        modifier to the "order by" clause. See
        https://www.w3.org/TR/2010/REC-xquery-20101214/#id-orderby-return for how to
        specify "order by" clauses.

        If "bm25-length-weight= NUMBER " is provided along with the "score-bm25" option,
        the BM25 scoring method is used with the weight specified. If the "score-bm25"
        option is provided but "bm25-length-weight= NUMBER " is not specified, the
        default value is 0.333. If provided, the value must be greater than 0.0 and less
        than or equal to 1.0. This value is used to calculate the BM25 score of each
        search result, and determines how much of an effect the document length to
        average document length ratio has on this score. Use lower values for
        "bm25-length-weight= NUMBER " to push the scores in favor of log(term frequency)
        and higher values to push the scores in favor of (document length / average
        document length). The optimal value for "bm25-length-weight= NUMBER " depends on
        your document collection. Experiment with this value to receive results that
        best fit your application.

        Native reference: https://docs.marklogic.com/cts:search
        """
        return _FunctionCall(
            "cts:search",
            (xpath("/") if expression is None else search_path(expression), query),
            (options, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def similar_query(nodes, *, weight=None, options=None) -> Expr:
        """Build a composable ``cts:similar-query`` call.

        Returns a query matching nodes similar to the model nodes.

        Parameters
        ----------
        nodes : node()*
            Some model nodes.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        options : element()?
            An XML representation of the options for defining which terms to generate
            and how to evaluate them. The options node must be in the
            cts:distinctive-terms namespace. The following is a sample options node :
            <options xmlns="cts:distinctive-terms"> <max-terms>20</max-terms> </options>
            See the cts:distinctive-terms options for the valid options to use with this
            function. Note that enabling index settings that are disabled in the
            database configuration will not affect the results, as similar documents
            will not be found on the basis of terms that do not exist in the actual
            database index.

        Returns
        -------
        Expr
            Composable call to ``cts:similar-query``.

        Notes
        -----
        cts:similar-query

        Native reference: https://docs.marklogic.com/cts:similar-query
        """
        return _FunctionCall(
            "cts:similar-query",
            (nodes,),
            (_double(weight), options),
        )

    @staticmethod
    def stddev(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:stddev`` call.

        Returns a frequency-weighted sample standard deviation given a value
        lexicon.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:stddev``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:stddev
        """
        return _FunctionCall(
            "cts:stddev",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def stddev_p(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:stddev-p`` call.

        Returns a frequency-weighted standard deviation of the population given
        a value lexicon.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:stddev-p``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:stddev-p
        """
        return _FunctionCall(
            "cts:stddev-p",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def stem(text, *, language=None, part_of_speech=None) -> Expr:
        """Build a composable ``cts:stem`` call.

        Returns the stem(s) for a word.

        Parameters
        ----------
        text : xs:string
            A word or phrase to stem.
        language : xs:string?
            A language to use for stemming. If not supplied, it uses the database
            default language.
        part_of_speech : xs:string?
            A part of speech to use for stemming. The default is the unspecified part of
            speech. This parameter is for testing custom stemmers.

        Returns
        -------
        Expr
            Composable call to ``cts:stem``.

        Notes
        -----
        In general, you should pass a word into cts:stem ; if you enter a phrase, it
        will stem the phrase, which will normally stem to itself.

        When you stem a word through cts:stem , it returns all of the stems for the
        word, including decompounding and multiple stems, regardless of the database
        stemming setting.

        Native reference: https://docs.marklogic.com/cts:stem
        """
        return _FunctionCall(
            "cts:stem",
            (text,),
            (language, part_of_speech),
        )

    @staticmethod
    def sum_aggregate(
        range_index,
        *,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:sum-aggregate`` call.

        Returns the sum of the values given a value lexicon.

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

        Returns
        -------
        Expr
            Composable call to ``cts:sum-aggregate``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:sum-aggregate
        """
        return _FunctionCall(
            "cts:sum-aggregate",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def thresholds(computed_labels, known_labels, *, recall_weight=None) -> Expr:
        """Build a composable ``cts:thresholds`` call.

        Compute precision, recall, the F measure, and thresholds for the classes
        computed by the classifier, by comparing with the labels for the same
        set.

        Parameters
        ----------
        computed_labels : element(cts:label)*
            A sequence of element nodes containing the labels from classification (the
            output from cts:classify ) for a set of documents.
        known_labels : element(cts:label)*
            A sequence of element nodes containing the known labels for the same set of
            documents.
        recall_weight : xs:double?
            The factor to use in the calculation of the F measure. The number should be
            non-negative. A value of 0 means F is just precision and a value of +INF
            means F is just recall. The default is 1, which gives the harmonic mean
            between precision and recall.

        Returns
        -------
        Expr
            Composable call to ``cts:thresholds``.

        Notes
        -----
        You use the output of cts:thresholds to determine the best thresholds values for
        your data, based on the first pass through the first part of your training data.
        The output of cts:thresholds provides you with precision and recall measurements
        at the calculated thresholds for each class. The following are the definitions
        of the attributes of the thresholds element returned by cts:thresholds :

        name The name of the class. threshold The threshold that is computed by the
        classifier to give the best results. The threshold is used by cts:classify when
        classifying documents, and is defined to be the positive or negative distance
        from the hyperplane which represents the edge of the class. precision A number
        which represents the fraction of nodes identified in a class that are actually
        in that class. As this approaches 1, there is a higher probability that you
        over-classified. recall A number which represents the fraction of nodes in a
        class that were identified by the classifier as being in that class. As this
        approaches 1, there is a higher probability that you under-classified. F (the
        F-measure) A measure which represents if the classification at the given
        threshold is closer to recall or closer to precision. A value of 1 indicates
        that precision and recall have equal weight. A value of 0.5 indicates that
        precision is weighted 2x recall. A value of 2 indicates that recall is weighted
        2x precision. A value of 0 indicates that the weighting is precision only, and a
        value of +INF ( xs:double('+INF')) indicates that weighting is recall only.

        Native reference: https://docs.marklogic.com/cts:thresholds
        """
        return _FunctionCall(
            "cts:thresholds",
            (computed_labels, known_labels),
            (_double(recall_weight),),
        )

    @staticmethod
    def tokenize(text, *, language=None, field=None) -> Expr:
        """Build a composable ``cts:tokenize`` call.

        Tokenizes text into words, punctuation, and spaces.

        Parameters
        ----------
        text : xs:string
            A word or phrase to tokenize.
        language : xs:string?
            A language to use for tokenization. If not supplied, it uses the database
            default language.
        field : xs:string?
            A field to use for tokenization. If the field has custom tokenization rules,
            they will be used. If no field is supplied or the field has no custom
            tokenization rules, the default tokenization rules are used.

        Returns
        -------
        Expr
            Composable call to ``cts:tokenize``.

        Notes
        -----
        When you tokenize a string with cts:tokenize , each word is represented by an
        instance of cts:word , each punctuation character is represented by an instance
        of cts:punctuation , each set of adjacent spaces is represented by an instance
        of cts:space , and each set of adjacent line breaks is represented by an
        instance of cts:space .

        Unlike the standard XQuery function fn:tokenize , cts:tokenize returns words,
        punctuation, and spaces as different types. You can therefore use a typeswitch
        to handle each type differently. For example, you can use cts:tokenize to remove
        all punctuation from a string, or create logic to test for the type and return
        different things for different types, as shown in the first two examples below.

        You can use xdmp:describe to show how a given string will be tokenized. When run
        on the results of cts:tokenize , the xdmp:describe function returns the types
        and the values for each token. For a sample of this pattern, see the third
        example below.

        Native reference: https://docs.marklogic.com/cts:tokenize
        """
        return _FunctionCall(
            "cts:tokenize",
            (text,),
            (language, field),
        )

    @staticmethod
    def train(training_nodes, labels, *, options=None) -> Expr:
        """Build a composable ``cts:train`` call.

        Produces a set of classifiers from a list of labeled training documents.

        Parameters
        ----------
        training_nodes : node()*
            The sequence of training nodes. These are nodes that represent members of
            the classes.
        labels : element(cts:label)*
            A sequence of labels for the training nodes, in the order corresponding to
            the training nodes.
        options : (element()|map:map)?
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

        Returns
        -------
        Expr
            Composable call to ``cts:train``.

        Notes
        -----
        The elements in the label sequence should match one for one with the nodes in
        the training node sequence. The first label element describes the first node in
        the training node sequence, the second label element describes the second node
        in the training node sequence, and so on. If there are more labels than training
        nodes or more training nodes than labels, an error is raised.

        The format of each label element is:

        <cts:label name="Node1"> <cts:class name="Example1"/> <cts:class name="Example2"
        val="-1"/> : : </cts:label>

        Each class listed indicates whether the corresponding node in the training
        sequence is in the given class. Examples are taken to be positive examples
        unless specified otherwise (with a val attribute of -1). The document is assumed
        to be a negative example of any classes that are not explicitly listed. The name
        attribute on the label element is an optional name for the labelled node. It is
        purely for human consumption to help in tuning the classification parameters.

        Output Formats

        A linear classifier is defined by a weight vector w on terms, and an offset
        value b. The <weights/> node encodes the weight vector directly. Its children
        are the classes, and each class includes a list of terms. The term node uses an
        internal id to identify the term and a term weight:

        <weights> <class name="Example1" offset="2.04"> <term id="43587329645324245"
        val="0.3423432"/> <term id="47893427895432534" val="-0.12345556"/> : : </class>
        : </weights>

        The weight vector w is a linear combination of the documents themselves, and it
        may be more convenient to express the classifier in this way. For instance, if
        the number of terms is not limited, the <weights/> node will be extremely large.
        The weight vector form may not be used if the classifier kernel is non-linear,
        that is, with the Gaussian or geodesic kernel.

        The support vector representation of the classifier includes a supports node
        that has <class/> children for each class. Here the class elements contain a
        list of doc elements which identify the specific training nodes using an
        internal key. This internal key is valid across queries only for nodes in the
        database. It is strongly recommended that the training set for supports
        classifiers consist of whole documents only. Each doc element has an attribute
        encoding the weight of that document and an error attribute which shows how well
        the document fit the classifier. Large positive or negative errors (greater than
        about 1.5) are potentially mis-classified documents.

        <supports> <class name="Example1" offset="2.04"> <doc id="155584958759"
        name="Node102" val="-0.00334163" err="1.4"/> <doc id="594064848864"
        name="Node57" val="0.025341234" err="-2.3"/> : : </class> : </supports>

        Each class is identified by a unique name.

        Native reference: https://docs.marklogic.com/cts:train
        """
        return _FunctionCall(
            "cts:train",
            (training_nodes, labels),
            (options,),
        )

    @staticmethod
    def triple_range_query(
        subject,
        predicate,
        object,
        *,
        operator=None,
        options=None,
        weight=None,
    ) -> Expr:
        """Build a composable ``cts:triple-range-query`` call.

        Returns a cts:query matching triples with a triple index entry equal to
        the given values.

        Parameters
        ----------
        subject : xs:anyAtomicType*
            The subjects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        predicate : xs:anyAtomicType*
            The predicates to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any predicate are matched.
        object : xs:anyAtomicType*
            The objects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any object are matched.
        operator : xs:string*
            One object operator or three subject/predicate/object operators.
            Includes sameTerm; empty sequences use the native default.
            MarkLogic validates these operators when the query is evaluated.
        options : xs:string*
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "score-function= function " Use the
            selected scoring function. The score function may be: linear Use a linear
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
        weight : xs:double?
            A weight for this query. The default is 1.0.

        Returns
        -------
        Expr
            Composable call to ``cts:triple-range-query``.

        Notes
        -----
        If you want to constrain on a range of values, you can combine multiple
        cts:triple-range-query constructors together with cts:and-query or any of the
        other composable cts:query constructors.

        If neither "cached" nor "uncached" is present, it specifies "cached".

        "score-function=linear" means that values that are further away from the bounds
        will score higher. "score-function=reciprocal" means that values that are closer
        to the bounds will score higher. The functions are scaled appropriately for
        different types, so that in general the default slope factor will provide useful
        results. Using a slope factor greater than 1 gives distinct scores over a
        smaller range of values, and produces generally higher scores. Using a slope
        factor less than 1 gives distinct scores over a wider range of values, and
        produces generally lower scores.

        Native reference: https://docs.marklogic.com/cts:triple-range-query
        """
        return _FunctionCall(
            "cts:triple-range-query",
            (subject, predicate, object),
            (
                operator,
                options,
                _double(weight),
            ),
        )

    @staticmethod
    def triple_value_statistics(*, values=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:triple-value-statistics`` call.

        Returns statistics from the triple index for the values given.

        Parameters
        ----------
        values : xs:anyAtomicType*
            The values to look up.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:triple-value-statistics``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:triple-value-statistics
        """
        return _FunctionCall(
            "cts:triple-value-statistics",
            (),
            (values, forest_ids),
        )

    @staticmethod
    def triples(
        *,
        subject=None,
        predicate=None,
        object=None,
        operator=None,
        options=None,
        query=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:triples`` call.

        Returns values from the triple index.

        Parameters
        ----------
        subject : xs:anyAtomicType*
            The subjects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        predicate : xs:anyAtomicType*
            The predicates to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        object : xs:anyAtomicType*
            The objects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        operator : xs:string*
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
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:triples``.

        Notes
        -----
        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "order-pso", "order-sop", or "order-ops" options may be
        specified in the options parameter. If none is specified, then the default is
        chosen to most efficiently retrieve the required values.

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        Native reference: https://docs.marklogic.com/cts:triples
        """
        return _FunctionCall(
            "cts:triples",
            (),
            (subject, predicate, object, operator, options, query, forest_ids),
        )

    @staticmethod
    def true_query() -> Expr:
        """Build a composable ``cts:true-query`` call.

        Returns a query that matches all fragments.

        Returns
        -------
        Expr
            Composable call to ``cts:true-query``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:true-query
        """
        return _FunctionCall(
            "cts:true-query",
            (),
        )

    @staticmethod
    def unordered() -> Expr:
        """Build a composable ``cts:unordered`` call.

        Specifies that results should be unordered, for use with cts:search.

        Returns
        -------
        Expr
            Composable call to ``cts:unordered``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:unordered
        """
        return _FunctionCall(
            "cts:unordered",
            (),
        )

    @staticmethod
    def uri_match(
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:uri-match`` call.

        Returns values from the URI lexicon that match the specified wildcard
        pattern.

        Parameters
        ----------
        pattern : xs:string
            Wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:uri-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "sample= N " is not specified in the options parameter, then all included
        URIs may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then URIs from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option as the skip is
        applied to the relevance ordered query matches, not to the ordered values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Native reference: https://docs.marklogic.com/cts:uri-match
        """
        return _FunctionCall(
            "cts:uri-match",
            (pattern,),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def uri_reference() -> Expr:
        """Build a composable ``cts:uri-reference`` call.

        Creates a reference to the URI lexicon, for use as a parameter to
        cts:value-tuples.

        Returns
        -------
        Expr
            Composable call to ``cts:uri-reference``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:uri-reference
        """
        return _FunctionCall(
            "cts:uri-reference",
            (),
        )

    @staticmethod
    def uris(
        query=None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:uris`` call.

        Returns values from the URI lexicon.

        Parameters
        ----------
        start : xs:string?
            A starting value. Return only this value and following values. If the empty
            string, return all values. If the parameter is not in the lexicon, then it
            returns the values beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include URIs from fragments selected by the cts:query , and compute
            frequencies from this set of included URIs. The fragments are not filtered
            to ensure they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:uris``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "sample= N " is not specified in the options parameter, then all included
        URIs may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then URIs from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option as the skip is
        applied to the relevance ordered query matches, not to the ordered values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:uris
        """
        return _FunctionCall(
            "cts:uris",
            (),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def valid_document_patch_path(string, *, map=None) -> Expr:
        """Build a composable ``cts:valid-document-patch-path`` call.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-document-patch-path``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:valid-document-patch-path
        """
        return _FunctionCall(
            "cts:valid-document-patch-path",
            (string,),
            (map,),
        )

    @staticmethod
    def valid_extract_path(string, *, map=None) -> Expr:
        """Build a composable ``cts:valid-extract-path`` call.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-extract-path``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:valid-extract-path
        """
        return _FunctionCall(
            "cts:valid-extract-path",
            (string,),
            (map,),
        )

    @staticmethod
    def valid_index_path(string, ignorens) -> Expr:
        """Build a composable ``cts:valid-index-path`` call.

        Parses path expressions and resolves namespaces based on the server run-
        time environment.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        ignorens : xs:boolean
            Ignore namespace prefix binding errors.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-index-path``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:valid-index-path
        """
        return _FunctionCall(
            "cts:valid-index-path",
            (string, ignorens),
        )

    @staticmethod
    def valid_optic_path(string, *, map=None) -> Expr:
        """Build a composable ``cts:valid-optic-path`` call.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-optic-path``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:valid-optic-path
        """
        return _FunctionCall(
            "cts:valid-optic-path",
            (string,),
            (map,),
        )

    @staticmethod
    def valid_tde_context(string, *, map=None) -> Expr:
        """Build a composable ``cts:valid-tde-context`` call.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : xs:string
            The path to be tested as a string.
        map : map:map?
            A map of namespace bindings. The keys should be namespace prefixes and the
            values should be namespace URIs. These namespace bindings will be added to
            the in-scope namespace bindings in the evaluation of the path.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-tde-context``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:valid-tde-context
        """
        return _FunctionCall(
            "cts:valid-tde-context",
            (string,),
            (map,),
        )

    @staticmethod
    def value_co_occurrences(
        range_index_1,
        range_index_2,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:value-co-occurrences`` call.

        Returns value co-occurrences (that is, pairs of values, both of which
        appear in the same fragment) from the specified value lexicon(s).

        Parameters
        ----------
        range_index_1 : cts:reference
            A reference to a range index.
        range_index_2 : cts:reference
            A reference to a range index.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:value-co-occurrences``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "map" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the co-occurrences returned by this function,
        use fn:subsequence on the output, rather than the "skip" option. The "skip"
        option is based on fragments matching the query parameter (if present), not on
        occurrences. A fragment matched by query might contain multiple occurrences or
        no occurrences. The number of fragments skipped does not correspond to the
        number of values. Also, the skip is applied to the relevance ordered query
        matches, not to the ordered co-occurrences list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:value-co-occurrences
        """
        return _FunctionCall(
            "cts:value-co-occurrences",
            (range_index_1, range_index_2),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def value_match(
        range_indexes,
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:value-match`` call.

        Returns values from the specified value lexicon(s) that match the
        specified wildcard pattern.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        pattern : xs:anyAtomicType
            A pattern to match. The parameter type must match the lexicon type. String
            parameters may include wildcard characters.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:value-match``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a range index with that collation does not exist, an error
        is thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Native reference: https://docs.marklogic.com/cts:value-match
        """
        return _FunctionCall(
            "cts:value-match",
            (range_indexes, pattern),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def value_ranges(
        range_indexes,
        *,
        bounds=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:value-ranges`` call.

        Returns value ranges from the specified value lexicon(s).

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        bounds : xs:anyAtomicType*
            A sequence of range bounds. The types must match the lexicon type. The
            values must be in strictly ascending order, otherwise an exception is
            thrown.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:value-ranges``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "eager" if
        "frequency-order" or "empties" is specified, otherwise "lazy".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then ranges with all
        included values may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        results list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:value-ranges
        """
        return _FunctionCall(
            "cts:value-ranges",
            (range_indexes,),
            (bounds, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def value_tuples(
        range_indexes,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:value-tuples`` call.

        Returns value co-occurrence tuples (that is, tuples of values, each of
        which appear in the same fragment) from the specified value lexicons.

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        options : xs:string*
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
        query : cts:query?
            Only include co-occurrences in fragments selected by the cts:query , and
            compute frequencies from this set of included co-occurrences. The
            co-occurrences do not need to match the query, but they must occur in
            fragments selected by the query. The fragments are not filtered to ensure
            they match the query, but instead selected in the same manner as
            "unfiltered" cts:search operations. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:value-tuples``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "eager" or "lazy" may be specified in the options parameter. If
        neither "eager" nor "lazy" is specified, then the default is "lazy" if
        "item-order" is specified, and "eager" if "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "sample= N " is not specified in the options parameter, then all included
        co-occurrences may be returned. If a $query parameter is not present, then
        "sample= N " has no effect.

        If "truncate= N " is not specified in the options parameter, then co-occurrences
        from all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the tuples returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple occurrences or no
        occurrences. The number of fragments skipped does not correspond to the number
        of tuples. Also, the skip is applied to the relevance ordered query matches, not
        to the ordered tuples list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:value-tuples
        """
        return _FunctionCall(
            "cts:value-tuples",
            (range_indexes,),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def values(
        range_indexes,
        query=None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:values`` call.

        Returns values from the specified value lexicon(s).

        Parameters
        ----------
        range_indexes : cts:reference*
            A sequence of references to range indexes.
        start : xs:anyAtomicType?
            A starting value. The parameter type must match the lexicon type. If the
            parameter value is not in the lexicon, then the values are returned
            beginning with the next value.
        options : xs:string*
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
        query : cts:query?
            Only include values in fragments selected by the cts:query , and compute
            frequencies from this set of included values. The values do not need to
            match the query, but they must occur in fragments selected by the query. The
            fragments are not filtered to ensure they match the query, but instead
            selected in the same manner as "unfiltered" cts:search operations. If a
            string is entered, the string is treated as a cts:word-query of the
            specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:values``.

        Notes
        -----
        Only one of "frequency-order" or "item-order" may be specified in the options
        parameter. If neither "frequency-order" nor "item-order" is specified, then the
        default is "item-order".

        Only one of "fragment-frequency" or "item-frequency" may be specified in the
        options parameter. If neither "fragment-frequency" nor "item-frequency" is
        specified, then the default is "fragment-frequency".

        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending" if "item-order" is specified, and "descending" if
        "frequency-order" is specified.

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        values may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then values from
        all fragments selected by the $query parameter are included. If a $query
        parameter is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:values
        """
        return _FunctionCall(
            "cts:values",
            (range_indexes,),
            (start, options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def variance(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:variance`` call.

        Returns a frequency-weighted sample variance given a value lexicon.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:variance``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:variance
        """
        return _FunctionCall(
            "cts:variance",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def variance_p(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:variance-p`` call.

        Returns a frequency-weighted variance of the population given a value
        lexicon.

        Parameters
        ----------
        range_index : cts:reference
            Reference to a range index. The type of the range index must be numeric.
        options : xs:string*
            Same as the "options" parameter in cts:aggregate .
        query : cts:query?
            Same as the "query" parameter in cts:aggregate .
        forest_ids : xs:unsignedLong*
            Same as the "forest-ids" parameter in cts:aggregate .

        Returns
        -------
        Expr
            Composable call to ``cts:variance-p``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/cts:variance-p
        """
        return _FunctionCall(
            "cts:variance-p",
            (range_index,),
            (options, query, forest_ids),
        )

    @staticmethod
    def walk(node, query, expr) -> Expr:
        """Build a composable ``cts:walk`` call.

        Walks a node, evaluating an expression with any text matching a query.

        Parameters
        ----------
        node : node()
            A node to walk. The node must be either a document node or an element node;
            it cannot be a text node.
        query : cts:query
            A query specifying the text on which to evaluate the expression. If a string
            is entered, the string is treated as a cts:word-query of the specified
            string.
        expr : item()*
            An expression to evaluate with matching text. You can use the variables
            $cts:text , $cts:node , $cts:queries , $cts:start , and $cts:action
            (described below) in the expression.

        Returns
        -------
        Expr
            Composable call to ``cts:walk``.

        Notes
        -----
        There are five built-in variables to represent a query match. These variables
        can be used inline in the expression parameter.

        $cts:text as xs:string The matched text. $cts:node as text() The node containing
        the matched text. $cts:queries as cts:query* The matching queries. $cts:start as
        xs:integer The string-length position of the first character of $cts:text in
        $cts:node . Therefore, the following always returns true:
        fn:substring($cts:node, $cts:start, fn:string-length($cts:text)) eq $cts:text
        $cts:action as xs:string Use xdmp:set on this to specify what should happen next
        "continue" (default) Walk the next match. If there are no more matches, return
        all evaluation results. "skip" Skip walking any more matches and return all
        evaluation results. "break" Stop walking matches and return all evaluation
        results.

        You cannot use cts:walk to walk results matching cts:similar-query and
        cts:element-attribute-*-query items.

        Because the expressions can be any XQuery expression, they can be very simple
        like the above example or they can be extremely complex.

        Unfiltered queries, including registered queries, do not match in cts:walk or
        cts:highlight .

        Native reference: https://docs.marklogic.com/cts:walk
        """
        return _FunctionCall(
            "cts:walk",
            (node, query, expr),
        )

    @staticmethod
    def word_match(
        pattern,
        *,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:word-match`` call.

        Returns words from the word lexicon that match the wildcard pattern.

        Parameters
        ----------
        pattern : xs:string
            A wildcard pattern to match.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:word-match``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        If neither "case-sensitive" nor "case-insensitive" is present, $pattern is used
        to determine case sensitivity. If $pattern contains no uppercase, it specifies
        "case-insensitive". If $pattern contains uppercase, it specifies
        "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present,
        $pattern is used to determine diacritic sensitivity. If $pattern contains no
        diacritics, it specifies "diacritic-insensitive". If $pattern contains
        diacritics, it specifies "diacritic-sensitive".

        Native reference: https://docs.marklogic.com/cts:word-match
        """
        return _FunctionCall(
            "cts:word-match",
            (pattern,),
            (options, query, _double(quality_weight), forest_ids),
        )

    @staticmethod
    def word_query(text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:word-query`` call.

        Returns a query matching text content containing a given phrase.

        Parameters
        ----------
        text : xs:string*
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : xs:string*
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard. "no-limit-check" is default, if neither "limit-check" nor
            "no-limit-check" is explicitly specified.
        weight : xs:double?
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.

        Returns
        -------
        Expr
            Composable call to ``cts:word-query``.

        Notes
        -----
        If neither "case-sensitive" nor "case-insensitive" is present, $text is used to
        determine case sensitivity. If $text contains no uppercase, it specifies
        "case-insensitive". If $text contains uppercase, it specifies "case-sensitive".

        If neither "diacritic-sensitive" nor "diacritic-insensitive" is present, $text
        is used to determine diacritic sensitivity. If $text contains no diacritics, it
        specifies "diacritic-insensitive". If $text contains diacritics, it specifies
        "diacritic-sensitive".

        If neither "punctuation-sensitive" nor "punctuation-insensitive" is present,
        $text is used to determine punctuation sensitivity. If $text contains no
        punctuation, it specifies "punctuation-insensitive". If $text contains
        punctuation, it specifies "punctuation-sensitive".

        If neither "whitespace-sensitive" nor "whitespace-insensitive" is present, the
        query is "whitespace-insensitive".

        If neither "wildcarded" nor "unwildcarded" is present, the database
        configuration and $text determine wildcarding. If the database has any wildcard
        indexes enabled ("three character searches", "two character searches", "one
        character searches", or "trailing wildcard searches") and if $text contains
        either of the wildcard characters '?' or '*', it specifies "wildcarded".
        Otherwise it specifies "unwildcarded".

        If neither "stemmed" nor "unstemmed" is present, the database configuration
        determines stemming. If the database has "stemmed searches" enabled, it
        specifies "stemmed". Otherwise it specifies "unstemmed". If the query is a
        wildcarded query and also a phrase query (contains two or more terms), the
        wildcard terms in the query are unstemmed.

        Negative "min-occurs" or "max-occurs" values will be treated as 0 and
        non-integral values will be rounded down. An error will be raised if the
        "min-occurs" value is greater than the "max-occurs" value.

        Relevance adjustment for the "distance-weight" option depends on the closest
        proximity of any two matches of the query. For example,
        cts:word-query(("dog","cat"),("distance-weight=10")) will adjust relevance based
        on the distance between the closest pair of matches of either "dog" or "cat"
        (the pair may consist only of matches of "dog", only of matches of "cat", or a
        match of "dog" and a match of "cat").

        Native reference: https://docs.marklogic.com/cts:word-query
        """
        return _FunctionCall(
            "cts:word-query",
            (text,),
            (options, _double(weight)),
        )

    @staticmethod
    def words(
        *,
        start=None,
        options=None,
        query=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build a composable ``cts:words`` call.

        Returns words from the word lexicon.

        Parameters
        ----------
        start : xs:string?
            A starting word. Returns only this word and any following words from the
            lexicon. If the parameter is not in the lexicon, then it returns the words
            beginning with the next word.
        options : xs:string*
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
        query : cts:query?
            Only include words in fragments selected by the cts:query . The words do not
            need to match the query, but the words must occur in fragments selected by
            the query. The fragments are not filtered to ensure they match the query,
            but instead selected in the same manner as "unfiltered" cts:search
            operations. If a string is entered, the string is treated as a
            cts:word-query of the specified string.
        quality_weight : xs:double?
            A document quality weight to use when computing scores. The default is 1.0.
        forest_ids : xs:unsignedLong*
            A sequence of IDs of forests to which the search will be constrained. An
            empty sequence means to search all forests in the database. The default is
            ().

        Returns
        -------
        Expr
            Composable call to ``cts:words``.

        Notes
        -----
        Only one of "ascending" or "descending" may be specified in the options
        parameter. If neither "ascending" nor "descending" is specified, then the
        default is "ascending".

        Only one of "any", "document", "properties", or "locks" may be specified in the
        options parameter. If none of "any", "document", "properties", or "locks" are
        specified and there is a $query parameter, then the default is "document". If
        there is no $query parameter then the default is "any".

        Only one of the "score-logtfidf", "score-logtf", "score-simple", "score-random",
        or "score-zero" options may be specified in the options parameter. If none of
        "score-logtfidf", "score-logtf", "score-simple", "score-random", or "score-zero"
        are specified, then the default is "score-logtfidf".

        Only one of the "checked" or "unchecked" options may be specified in the options
        parameter. If neither "checked" nor "unchecked" are specified, then the default
        is "checked".

        If "collation= URI " is not specified in the options parameter, then the default
        collation is used. If a lexicon with that collation does not exist, an error is
        thrown.

        If "sample= N " is not specified in the options parameter, then all included
        words may be returned. If a $query parameter is not present, then "sample= N "
        has no effect.

        If "truncate= N " is not specified in the options parameter, then words from all
        fragments selected by the $query parameter are included. If a $query parameter
        is not present, then "truncate= N " has no effect.

        To incrementally fetch a subset of the values returned by this function, use
        fn:subsequence on the output, rather than the "skip" option. The "skip" option
        is based on fragments matching the query parameter (if present), not on values.
        A fragment matched by query might contain multiple values or no values. The
        number of fragments skipped does not correspond to the number of values. Also,
        the skip is applied to the relevance ordered query matches, not to the ordered
        values list.

        When using the "skip" option, use the "truncate" option rather than the "limit"
        option to control the number of matching fragments from which to draw values.

        Native reference: https://docs.marklogic.com/cts:words
        """
        return _FunctionCall(
            "cts:words",
            (),
            (start, options, query, _double(quality_weight), forest_ids),
        )
