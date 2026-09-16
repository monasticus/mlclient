# ruff: noqa: A002, PLR0913
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
    search_path,
    xpath,
)
from mlclient.functions.xqy._xs import Xs

xs = Xs()

_RANGE_OPERATORS = frozenset({"<", "<=", ">", ">=", "=", "!="})
_DIRECTORY_DEPTHS = frozenset({"1", "infinity"})


def _weight(value) -> Expr | None:
    """Cast an optional numeric weight to the native double type."""
    return xs.double(value) if value is not None else None


def _qname(value) -> Expr:
    """Convert local-name strings, QName expressions or their sequences."""
    if isinstance(value, (list, tuple)):
        return as_expr(tuple(_qname(item) for item in value))
    return value if isinstance(value, Expr) else xs.qname(value)


def _operator(value) -> Expr:
    """Validate a literal range comparison operator; expressions stay composable."""
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


def _point_coordinate(value) -> Expr:
    """Keep WKT strings intact and cast numeric point coordinates to float."""
    if isinstance(value, (str, Expr)):
        return as_expr(value)
    return as_expr(value, cast="xs:float")


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
            Value for native ``$timestamp`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:after-query``.
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
            Value for native ``$native-plugin`` parameter.
        aggregate_name : xs:string
            Value for native ``$aggregate-name`` parameter.
        range_indexes : cts:reference*
            Value for native ``$range-indexes`` parameter.
        argument : item()*
            Value for native ``$argument`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:aggregate``.
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
            Value for native ``$positive-query`` parameter.
        negative_query : cts:query
            Value for native ``$negative-query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:and-not-query``.
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
            Value for native ``$queries`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:and-query``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:avg-aggregate``.
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
            Value for native ``$timestamp`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:before-query``.
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
            Value for native ``$matching-query`` parameter.
        boosting_query : cts:query
            Value for native ``$boosting-query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:boost-query``.
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
            Value for native ``$south`` parameter.
        west : xs:float
            Value for native ``$west`` parameter.
        north : xs:float
            Value for native ``$north`` parameter.
        east : xs:float
            Value for native ``$east`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:box``.
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
            Value for native ``$radius`` parameter.
        center : cts:point
            Value for native ``$center`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:circle``.
        """
        return _FunctionCall(
            "cts:circle",
            (_weight(radius), center),
        )

    @staticmethod
    def classify(data_nodes, classifier, *, options=None, training_nodes=None) -> Expr:
        """Build a composable ``cts:classify`` call.

        Classifies a sequence of nodes based on training data.

        Parameters
        ----------
        data_nodes : node()*
            Value for native ``$data-nodes`` parameter.
        classifier : element(cts:classifier)
            Value for native ``$classifier`` parameter.
        options : (element()|map:map)?
            Value for native ``$options`` parameter.
        training_nodes : node()*
            Value for native ``$training-nodes`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:classify``.
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
            Value for native ``$nodes`` parameter.
        options : (element()|map:map)?
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:cluster``.
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
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:collection-match``.
        """
        return _FunctionCall(
            "cts:collection-match",
            (pattern,),
            (options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def collection_query(uris) -> Expr:
        """Build a composable ``cts:collection-query`` call.

        Match documents in at least one of the specified collections.

        Parameters
        ----------
        uris : xs:string*
            Value for native ``$uris`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:collection-query``.
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
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:collection-reference``.
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
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:collections``.
        """
        return _FunctionCall(
            "cts:collections",
            (),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$schema`` parameter.
        view : xs:string
            Value for native ``$view`` parameter.
        column : xs:string
            Value for native ``$column`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        operator : xs:string?
            Value for native ``$operator`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:column-range-query``.
        """
        return _FunctionCall(
            "cts:column-range-query",
            (schema, view, column, value),
            (
                _operator(operator) if operator is not None else None,
                options,
                _weight(weight),
            ),
        )

    @staticmethod
    def complex_polygon(outer, inner) -> Expr:
        """Build a composable ``cts:complex-polygon`` call.

        Returns a geospatial complex polygon value.

        Parameters
        ----------
        outer : cts:polygon
            Value for native ``$outer`` parameter.
        inner : cts:polygon*
            Value for native ``$inner`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:complex-polygon``.
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
            Value for native ``$node`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:confidence``.
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
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:confidence-order``.
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
            Value for native ``$nodes`` parameter.
        query : cts:query
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:contains``.
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
            Value for native ``$value1`` parameter.
        value2 : cts:reference
            Value for native ``$value2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:correlation``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:count-aggregate``.
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
            Value for native ``$value1`` parameter.
        value2 : cts:reference
            Value for native ``$value2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:covariance``.
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
            Value for native ``$value1`` parameter.
        value2 : cts:reference
            Value for native ``$value2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:covariance-p``.
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
            Value for native ``$id`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:deregister``.
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
            Value for native ``$uris`` parameter.
        depth : xs:string?
            Value for native ``$depth`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:directory-query``.
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
            Value for native ``$nodes`` parameter.
        options : element()?
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:distinctive-terms``.
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
            Value for native ``$format`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:document-format-query``.
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
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:document-fragment-query``.
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
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:document-order``.
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
            Value for native ``$role`` parameter.
        capability : xs:string
            Value for native ``$capability`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:document-permission-query``.
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
            Value for native ``$uris`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:document-query``.
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
            Value for native ``$root`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:document-root-query``.
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
            Value for native ``$parent-element-names`` parameter.
        latitude_names : xs:QName*
            Value for native ``$latitude-names`` parameter.
        longitude_names : xs:QName*
            Value for native ``$longitude-names`` parameter.
        latitude_bounds : xs:double*
            Value for native ``$latitude-bounds`` parameter.
        longitude_bounds : xs:double*
            Value for native ``$longitude-bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-boxes``.
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
                _weight(quality_weight),
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
            Value for native ``$element-name`` parameter.
        latitude_attribute_names : xs:QName*
            Value for native ``$latitude-attribute-names`` parameter.
        longitude_attribute_names : xs:QName*
            Value for native ``$longitude-attribute-names`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-query``.
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-query",
            (
                _qname(element_name),
                _qname(latitude_attribute_names),
                _qname(longitude_attribute_names),
                regions,
            ),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        latitude_names : xs:QName*
            Value for native ``$latitude-names`` parameter.
        longitude_names : xs:QName*
            Value for native ``$longitude-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-value-match``.
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-value-match",
            (
                _qname(element_names),
                _qname(latitude_names),
                _qname(longitude_names),
                pattern,
            ),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        latitude_names : xs:QName*
            Value for native ``$latitude-names`` parameter.
        longitude_names : xs:QName*
            Value for native ``$longitude-names`` parameter.
        start : cts:point?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-pair-geospatial-values``.
        """
        return _FunctionCall(
            "cts:element-attribute-pair-geospatial-values",
            (_qname(element_names), _qname(latitude_names), _qname(longitude_names)),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-name`` parameter.
        attribute_name : xs:QName*
            Value for native ``$attribute-name`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-range-query``.
        """
        return _FunctionCall(
            "cts:element-attribute-range-query",
            (_qname(element_name), _qname(attribute_name), _operator(operator), value),
            (options, _weight(weight)),
        )

    @staticmethod
    def element_attribute_reference(element, attribute, *, options=None) -> Expr:
        """Build a composable ``cts:element-attribute-reference`` call.

        Creates a reference to an element attribute value lexicon, for use as a
        parameter to cts:value-tuples.

        Parameters
        ----------
        element : xs:QName
            Value for native ``$element`` parameter.
        attribute : xs:QName
            Value for native ``$attribute`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-reference``.
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
            Value for native ``$element-name-1`` parameter.
        attribute_name_1 : xs:QName?
            Value for native ``$attribute-name-1`` parameter.
        element_name_2 : xs:QName
            Value for native ``$element-name-2`` parameter.
        attribute_name_2 : xs:QName?
            Value for native ``$attribute-name-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-co-occurrences``.
        """
        return _FunctionCall(
            "cts:element-attribute-value-co-occurrences",
            (
                _qname(element_name_1),
                _qname(attribute_name_1),
                _qname(element_name_2),
                _qname(attribute_name_2),
            ),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-name-1`` parameter.
        attribute_name_1 : xs:QName?
            Value for native ``$attribute-name-1`` parameter.
        geo_element_name : xs:QName
            Value for native ``$geo-element-name`` parameter.
        coord_child_name_1 : xs:QName?
            Value for native ``$coord-child-name-1`` parameter.
        coord_child_name_2 : xs:QName?
            Value for native ``$coord-child-name-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable ``cts:element-attribute-value-geospatial-co-occurrences``
            call.
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
                _weight(quality_weight),
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
            Value for native ``$element-names`` parameter.
        attribute_names : xs:QName*
            Value for native ``$attribute-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-match``.
        """
        return _FunctionCall(
            "cts:element-attribute-value-match",
            (_qname(element_names), _qname(attribute_names), pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-name`` parameter.
        attribute_name : xs:QName*
            Value for native ``$attribute-name`` parameter.
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-query``.
        """
        return _FunctionCall(
            "cts:element-attribute-value-query",
            (_qname(element_name), _qname(attribute_name), text),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        attribute_names : xs:QName*
            Value for native ``$attribute-names`` parameter.
        bounds : xs:anyAtomicType*
            Value for native ``$bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-value-ranges``.
        """
        return _FunctionCall(
            "cts:element-attribute-value-ranges",
            (_qname(element_names), _qname(attribute_names)),
            (bounds, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        attribute_names : xs:QName*
            Value for native ``$attribute-names`` parameter.
        start : xs:anyAtomicType?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-values``.
        """
        return _FunctionCall(
            "cts:element-attribute-values",
            (_qname(element_names), _qname(attribute_names)),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        attribute_names : xs:QName*
            Value for native ``$attribute-names`` parameter.
        pattern : xs:string
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-word-match``.
        """
        return _FunctionCall(
            "cts:element-attribute-word-match",
            (_qname(element_names), _qname(attribute_names), pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-name`` parameter.
        attribute_name : xs:QName*
            Value for native ``$attribute-name`` parameter.
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-word-query``.
        """
        return _FunctionCall(
            "cts:element-attribute-word-query",
            (_qname(element_name), _qname(attribute_name), text),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        attribute_names : xs:QName*
            Value for native ``$attribute-names`` parameter.
        start : xs:string?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-attribute-words``.
        """
        return _FunctionCall(
            "cts:element-attribute-words",
            (_qname(element_names), _qname(attribute_names)),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$parent-element-names`` parameter.
        child_element_names : xs:QName*
            Value for native ``$child-element-names`` parameter.
        latitude_bounds : xs:double*
            Value for native ``$latitude-bounds`` parameter.
        longitude_bounds : xs:double*
            Value for native ``$longitude-bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-boxes``.
        """
        return _FunctionCall(
            "cts:element-child-geospatial-boxes",
            (_qname(parent_element_names), _qname(child_element_names)),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _weight(quality_weight),
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
            Value for native ``$parent-element-name`` parameter.
        child_element_names : xs:QName*
            Value for native ``$child-element-names`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-query``.
        """
        return _FunctionCall(
            "cts:element-child-geospatial-query",
            (_qname(parent_element_name), _qname(child_element_names), regions),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        child_names : xs:QName*
            Value for native ``$child-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-value-match``.
        """
        return _FunctionCall(
            "cts:element-child-geospatial-value-match",
            (_qname(element_names), _qname(child_names), pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        child_names : xs:QName*
            Value for native ``$child-names`` parameter.
        start : cts:point?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-child-geospatial-values``.
        """
        return _FunctionCall(
            "cts:element-child-geospatial-values",
            (_qname(element_names), _qname(child_names)),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        latitude_bounds : xs:double*
            Value for native ``$latitude-bounds`` parameter.
        longitude_bounds : xs:double*
            Value for native ``$longitude-bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-boxes``.
        """
        return _FunctionCall(
            "cts:element-geospatial-boxes",
            (_qname(element_names),),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _weight(quality_weight),
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
            Value for native ``$element-name`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-query``.
        """
        return _FunctionCall(
            "cts:element-geospatial-query",
            (_qname(element_name), regions),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-value-match``.
        """
        return _FunctionCall(
            "cts:element-geospatial-value-match",
            (_qname(element_names), pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        start : cts:point?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-geospatial-values``.
        """
        return _FunctionCall(
            "cts:element-geospatial-values",
            (_qname(element_names),),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$parent-element-names`` parameter.
        latitude_names : xs:QName*
            Value for native ``$latitude-names`` parameter.
        longitude_names : xs:QName*
            Value for native ``$longitude-names`` parameter.
        latitude_bounds : xs:double*
            Value for native ``$latitude-bounds`` parameter.
        longitude_bounds : xs:double*
            Value for native ``$longitude-bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-boxes``.
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
                _weight(quality_weight),
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
            Value for native ``$element-name`` parameter.
        latitude_element_names : xs:QName*
            Value for native ``$latitude-element-names`` parameter.
        longitude_element_names : xs:QName*
            Value for native ``$longitude-element-names`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-query``.
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-query",
            (
                _qname(element_name),
                _qname(latitude_element_names),
                _qname(longitude_element_names),
                regions,
            ),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        latitude_names : xs:QName*
            Value for native ``$latitude-names`` parameter.
        longitude_names : xs:QName*
            Value for native ``$longitude-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-value-match``.
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-value-match",
            (
                _qname(element_names),
                _qname(latitude_names),
                _qname(longitude_names),
                pattern,
            ),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        latitude_names : xs:QName*
            Value for native ``$latitude-names`` parameter.
        longitude_names : xs:QName*
            Value for native ``$longitude-names`` parameter.
        start : cts:point?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-pair-geospatial-values``.
        """
        return _FunctionCall(
            "cts:element-pair-geospatial-values",
            (_qname(element_names), _qname(latitude_names), _qname(longitude_names)),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def element_query(element_name, query) -> Expr:
        """Build a composable ``cts:element-query`` call.

        Constructs a query that matches elements by name with the content
        constrained by the query given in the second parameter.

        Parameters
        ----------
        element_name : xs:QName*
            Value for native ``$element-name`` parameter.
        query : cts:query
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-query``.
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
            Value for native ``$element-name`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-range-query``.
        """
        return _FunctionCall(
            "cts:element-range-query",
            (_qname(element_name), _operator(operator), value),
            (options, _weight(weight)),
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
            Value for native ``$element`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-reference``.
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
            Value for native ``$element-name-1`` parameter.
        element_name_2 : xs:QName
            Value for native ``$element-name-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-co-occurrences``.
        """
        return _FunctionCall(
            "cts:element-value-co-occurrences",
            (_qname(element_name_1), _qname(element_name_2)),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-name-1`` parameter.
        geo_element_name : xs:QName
            Value for native ``$geo-element-name`` parameter.
        coord_child_name_1 : xs:QName?
            Value for native ``$coord-child-name-1`` parameter.
        coord_child_name_2 : xs:QName?
            Value for native ``$coord-child-name-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-geospatial-co-occurrences``.
        """
        return _FunctionCall(
            "cts:element-value-geospatial-co-occurrences",
            (_qname(element_name_1), _qname(geo_element_name)),
            (
                _qname(coord_child_name_1) if coord_child_name_1 is not None else None,
                _qname(coord_child_name_2) if coord_child_name_2 is not None else None,
                options,
                query,
                _weight(quality_weight),
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
            Value for native ``$element-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-match``.
        """
        return _FunctionCall(
            "cts:element-value-match",
            (_qname(element_names), pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-name`` parameter.
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-query``.
        """
        return _FunctionCall(
            "cts:element-value-query",
            (_qname(element_name),),
            (text, options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        bounds : xs:anyAtomicType*
            Value for native ``$bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-value-ranges``.
        """
        return _FunctionCall(
            "cts:element-value-ranges",
            (_qname(element_names),),
            (bounds, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$element-names`` parameter.
        start : xs:anyAtomicType?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-values``.
        """
        return _FunctionCall(
            "cts:element-values",
            (_qname(element_names),),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def element_walk(node, element, expr) -> Expr:
        """Build a composable ``cts:element-walk`` call.

        Returns a copy of the node, replacing any elements found with the
        specified expression.

        Parameters
        ----------
        node : node()
            Value for native ``$node`` parameter.
        element : xs:QName*
            Value for native ``$element`` parameter.
        expr : item()*
            Value for native ``$expr`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-walk``.
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
            Value for native ``$element-names`` parameter.
        pattern : xs:string?
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-word-match``.
        """
        return _FunctionCall(
            "cts:element-word-match",
            (_qname(element_names), pattern),
            (options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def element_word_query(element_name, text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:element-word-query`` call.

        Returns a query matching elements by name with text content containing a
        given phrase.

        Parameters
        ----------
        element_name : xs:QName*
            Value for native ``$element-name`` parameter.
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-word-query``.
        """
        return _FunctionCall(
            "cts:element-word-query",
            (_qname(element_name), text),
            (options, _weight(weight)),
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
            Value for native ``$element-names`` parameter.
        start : xs:string?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:element-words``.
        """
        return _FunctionCall(
            "cts:element-words",
            (_qname(element_names),),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def entity(id, normalized_text, text, type) -> Expr:
        """Build a composable ``cts:entity`` call.

        Returns a cts:entity object.

        Parameters
        ----------
        id : xs:string
            Value for native ``$id`` parameter.
        normalized_text : xs:string
            Value for native ``$normalizedText`` parameter.
        text : xs:string
            Value for native ``$text`` parameter.
        type : xs:string
            Value for native ``$type`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:entity``.
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
            Value for native ``$entities`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-dictionary``.
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
            Value for native ``$contents`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-dictionary-parse``.
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
            Value for native ``$node`` parameter.
        expr : item()*
            Value for native ``$expr`` parameter.
        dict : cts:entity-dictionary
            Value for native ``$dict`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-highlight``.
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
            Value for native ``$node`` parameter.
        expr : item()*
            Value for native ``$expr`` parameter.
        dict : cts:entity-dictionary
            Value for native ``$dict`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:entity-walk``.
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
            Value for native ``$query`` parameter.
        options : (cts:order|xs:string)*
            Value for native ``$options`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.
        maximum : xs:double?
            Value for native ``$maximum`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:estimate``.
        """
        return _FunctionCall(
            "cts:estimate",
            (),
            (query, options, _weight(quality_weight), forest_ids, _weight(maximum)),
        )

    @staticmethod
    def false_query() -> Expr:
        """Build a composable ``cts:false-query`` call.

        Returns a query that matches no fragments.

        Returns
        -------
        Expr
            Composable call to ``cts:false-query``.
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
            Value for native ``$field-name`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-range-query``.
        """
        return _FunctionCall(
            "cts:field-range-query",
            (field_name, _operator(operator), value),
            (options, _weight(weight)),
        )

    @staticmethod
    def field_reference(field, *, options=None) -> Expr:
        """Build a composable ``cts:field-reference`` call.

        Creates a reference to a field value lexicon, for use as a parameter to
        cts:value-tuples.

        Parameters
        ----------
        field : xs:string
            Value for native ``$field`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-reference``.
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
            Value for native ``$field-name-1`` parameter.
        field_name_2 : xs:string
            Value for native ``$field-name-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-co-occurrences``.
        """
        return _FunctionCall(
            "cts:field-value-co-occurrences",
            (field_name_1, field_name_2),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$field-names`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-match``.
        """
        return _FunctionCall(
            "cts:field-value-match",
            (field_names, pattern),
            (options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def field_value_query(field_name, text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:field-value-query`` call.

        Returns a query matching text content containing a given value in the
        specified field.

        Parameters
        ----------
        field_name : xs:string*
            Value for native ``$field-name`` parameter.
        text : xs:anyAtomicType*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-query``.
        """
        return _FunctionCall(
            "cts:field-value-query",
            (field_name, text),
            (options, _weight(weight)),
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
            Value for native ``$field-names`` parameter.
        bounds : xs:anyAtomicType*
            Value for native ``$bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-value-ranges``.
        """
        return _FunctionCall(
            "cts:field-value-ranges",
            (field_names,),
            (bounds, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$field-names`` parameter.
        start : xs:anyAtomicType?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-values``.
        """
        return _FunctionCall(
            "cts:field-values",
            (field_names,),
            (start, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$field-names`` parameter.
        pattern : xs:string
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-word-match``.
        """
        return _FunctionCall(
            "cts:field-word-match",
            (field_names, pattern),
            (options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def field_word_query(field_name, text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:field-word-query`` call.

        Returns a query matching fields with text content containing a given
        phrase.

        Parameters
        ----------
        field_name : xs:string*
            Value for native ``$field-name`` parameter.
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-word-query``.
        """
        return _FunctionCall(
            "cts:field-word-query",
            (field_name, text),
            (options, _weight(weight)),
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
            Value for native ``$field-names`` parameter.
        start : xs:string?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:field-words``.
        """
        return _FunctionCall(
            "cts:field-words",
            (field_names,),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def fitness(*, node=None) -> Expr:
        """Build a composable ``cts:fitness`` call.

        Returns the fitness of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : node()
            Value for native ``$node`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:fitness``.
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
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:fitness-order``.
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
            Value for native ``$value`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:frequency``.
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
            Value for native ``$element`` parameter.
        lat : xs:QName
            Value for native ``$lat`` parameter.
        long : xs:QName
            Value for native ``$long`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-attribute-pair-reference``.
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
            Value for native ``$geo-indexes`` parameter.
        latitude_bounds : xs:double*
            Value for native ``$latitude-bounds`` parameter.
        longitude_bounds : xs:double*
            Value for native ``$longitude-bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-boxes``.
        """
        return _FunctionCall(
            "cts:geospatial-boxes",
            (geo_indexes,),
            (
                latitude_bounds,
                longitude_bounds,
                options,
                query,
                _weight(quality_weight),
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
            Value for native ``$geo-element-name-1`` parameter.
        child_1_name_1 : xs:QName?
            Value for native ``$child-1-name-1`` parameter.
        child_1_name_2 : xs:QName?
            Value for native ``$child-1-name-2`` parameter.
        geo_element_name_2 : xs:QName
            Value for native ``$geo-element-name-2`` parameter.
        child_2_name_1 : xs:QName?
            Value for native ``$child-2-name-1`` parameter.
        child_2_name_2 : xs:QName?
            Value for native ``$child-2-name-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-co-occurrences``.
        """
        return _FunctionCall(
            "cts:geospatial-co-occurrences",
            (_qname(geo_element_name_1), _qname(geo_element_name_2)),
            (
                _qname(child_1_name_1) if child_1_name_1 is not None else None,
                _qname(child_1_name_2) if child_1_name_2 is not None else None,
                _qname(child_2_name_1) if child_2_name_1 is not None else None,
                _qname(child_2_name_2) if child_2_name_2 is not None else None,
                options,
                query,
                _weight(quality_weight),
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
            Value for native ``$element`` parameter.
        child : xs:QName
            Value for native ``$child`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-element-child-reference``.
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
            Value for native ``$element`` parameter.
        lat : xs:QName
            Value for native ``$lat`` parameter.
        long : xs:QName
            Value for native ``$long`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-element-pair-reference``.
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
            Value for native ``$element`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-element-reference``.
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
            Value for native ``$property`` parameter.
        child : xs:string
            Value for native ``$child`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-json-property-child-reference``.
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
            Value for native ``$property`` parameter.
        lat : xs:string
            Value for native ``$lat`` parameter.
        long : xs:string
            Value for native ``$long`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-json-property-pair-reference``.
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
            Value for native ``$property`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-json-property-reference``.
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
            Value for native ``$path-expression`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        map : map:map
            Value for native ``$map`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-path-reference``.
        """
        return _FunctionCall(
            "cts:geospatial-path-reference",
            (path_expression,),
            (options, map),
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
            Value for native ``$path-expression`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        namespaces : map:map
            Value for native ``$namespaces`` parameter.
        geohash_precision : xs:integer?
            Value for native ``$geohash-precision`` parameter.
        units : xs:string?
            Value for native ``$units`` parameter.
        invalid_values : xs:string?
            Value for native ``$invalid-values`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-region-path-reference``.
        """
        return _FunctionCall(
            "cts:geospatial-region-path-reference",
            (path_expression,),
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
            Value for native ``$geospatial-region-reference`` parameter.
        operation : xs:string
            Value for native ``$operation`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:geospatial-region-query``.
        """
        return _FunctionCall(
            "cts:geospatial-region-query",
            (geospatial_region_reference, operation, regions),
            (options, _weight(weight)),
        )

    @staticmethod
    def highlight(node, query, expr) -> Expr:
        """Build a composable ``cts:highlight`` call.

        Returns a copy of the node, replacing any text matching the query with
        the specified expression.

        Parameters
        ----------
        node : node()
            Value for native ``$node`` parameter.
        query : cts:query
            Value for native ``$query`` parameter.
        expr : item()*
            Value for native ``$expr`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:highlight``.
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
            Value for native ``$index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:index-order``.
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
            Value for native ``$parent-property-name`` parameter.
        child_property_names : xs:string*
            Value for native ``$child-property-names`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-child-geospatial-query``.
        """
        return _FunctionCall(
            "cts:json-property-child-geospatial-query",
            (parent_property_name, child_property_names, regions),
            (options, _weight(weight)),
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
            Value for native ``$property-name`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-geospatial-query``.
        """
        return _FunctionCall(
            "cts:json-property-geospatial-query",
            (property_name, regions),
            (options, _weight(weight)),
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
            Value for native ``$property-name`` parameter.
        latitude_property_names : xs:string*
            Value for native ``$latitude-property-names`` parameter.
        longitude_property_names : xs:string*
            Value for native ``$longitude-property-names`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-pair-geospatial-query``.
        """
        return _FunctionCall(
            "cts:json-property-pair-geospatial-query",
            (property_name, latitude_property_names, longitude_property_names, regions),
            (options, _weight(weight)),
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
            Value for native ``$property-name`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-range-query``.
        """
        return _FunctionCall(
            "cts:json-property-range-query",
            (property_name, _operator(operator), value),
            (options, _weight(weight)),
        )

    @staticmethod
    def json_property_reference(property, *, options=None) -> Expr:
        """Build a composable ``cts:json-property-reference`` call.

        Creates a reference to a JSON property value lexicon, for use as a
        parameter to cts:value-tuples.

        Parameters
        ----------
        property : xs:string
            Value for native ``$property`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-reference``.
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
            Value for native ``$property-name`` parameter.
        query : cts:query
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-scope-query``.
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
            Value for native ``$property-name`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-value-query``.
        """
        return _FunctionCall(
            "cts:json-property-value-query",
            (property_name, value),
            (options, _weight(weight)),
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
            Value for native ``$property-names`` parameter.
        pattern : xs:string?
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-word-match``.
        """
        return _FunctionCall(
            "cts:json-property-word-match",
            (property_names, pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$property-name`` parameter.
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-word-query``.
        """
        return _FunctionCall(
            "cts:json-property-word-query",
            (property_name, text),
            (options, _weight(weight)),
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
            Value for native ``$property-names`` parameter.
        start : xs:string?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:json-property-words``.
        """
        return _FunctionCall(
            "cts:json-property-words",
            (property_names,),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def linear_model(values, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:linear-model`` call.

        Returns a linear model that fits the frequency-weighted data set.

        Parameters
        ----------
        values : cts:reference*
            Value for native ``$values`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:linear-model``.
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
            Value for native ``$vertices`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:linestring``.
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
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:locks-fragment-query``.
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
            Value for native ``$temporal-collection`` parameter.
        timestamp : xs:dateTime?
            Value for native ``$timestamp`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:lsqt-query``.
        """
        return _FunctionCall(
            "cts:lsqt-query",
            (temporal_collection,),
            (timestamp, options, _weight(weight)),
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
            Value for native ``$range-indexes`` parameter.
        operation : xs:string
            Value for native ``$operation`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:match-regions``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:max``.
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
            Value for native ``$arg`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:median``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:min``.
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
            Value for native ``$queries`` parameter.
        distance : xs:double?
            Value for native ``$distance`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        distance_weight : xs:double?
            Value for native ``$distance-weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:near-query``.
        """
        return _FunctionCall(
            "cts:near-query",
            (queries,),
            (_weight(distance), options, _weight(distance_weight)),
        )

    @staticmethod
    def not_in_query(positive_query, negative_query) -> Expr:
        """Build a composable ``cts:not-in-query`` call.

        Returns a query matching the first sub-query, where those matches do not
        occur within 0 distance of the other query.

        Parameters
        ----------
        positive_query : cts:query
            Value for native ``$positive-query`` parameter.
        negative_query : cts:query
            Value for native ``$negative-query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:not-in-query``.
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
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:not-query``.
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
            Value for native ``$queries`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:or-query``.
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
            Value for native ``$query`` parameter.
        bindings : map:map?
            Value for native ``$bindings`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:parse``.
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
            Value for native ``$token`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:part-of-speech``.
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
            Value for native ``$path-expression`` parameter.
        regions : cts:region*
            Value for native ``$regions`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:path-geospatial-query``.
        """
        return _FunctionCall(
            "cts:path-geospatial-query",
            (path_expression, regions),
            (options, _weight(weight)),
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
            Value for native ``$path-expression`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:path-range-query``.
        """
        return _FunctionCall(
            "cts:path-range-query",
            (path_expression, _operator(operator), value),
            (options, _weight(weight)),
        )

    @staticmethod
    def path_reference(path_expression, *, options=None, namespaces=None) -> Expr:
        """Build a composable ``cts:path-reference`` call.

        Creates a reference to a path value lexicon, for use as a parameter to
        cts:value-tuples.

        Parameters
        ----------
        path_expression : xs:string
            Value for native ``$path-expression`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        namespaces : map:map
            Value for native ``$map`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:path-reference``.
        """
        return _FunctionCall(
            "cts:path-reference",
            (path_expression,),
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
            Value for native ``$arg`` parameter.
        value : xs:anyAtomicType
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:percent-rank``.
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
            Value for native ``$arg`` parameter.
        p : xs:double*
            Value for native ``$p`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:percentile``.
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
            Value for native ``$start`` parameter.
        end : xs:dateTime
            Value for native ``$end`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:period``.
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
            Value for native ``$period-1`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        period_2 : cts:period
            Value for native ``$period-2`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:period-compare``.
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
            Value for native ``$axis-1`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        axis_2 : xs:string
            Value for native ``$axis-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:period-compare-query``.
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
            Value for native ``$axis-name`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        period : cts:period*
            Value for native ``$period`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:period-range-query``.
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
            Value for native ``$latitude-or-wkt`` parameter.
        longitude : xs:float
            Value for native ``$longitude`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:point``.
        """
        return _FunctionCall(
            "cts:point",
            (_point_coordinate(latitude_or_wkt),),
            (_point_coordinate(longitude) if longitude is not None else None,),
        )

    @staticmethod
    def polygon(vertices) -> Expr:
        """Build a composable ``cts:polygon`` call.

        Returns a geospatial polygon value.

        Parameters
        ----------
        vertices : (cts:point*|xs:string)
            Value for native ``$vertices`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:polygon``.
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
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:properties-fragment-query``.
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
            Value for native ``$node`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:quality``.
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
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:quality-order``.
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
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:query``.
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
            Value for native ``$index`` parameter.
        operator : xs:string
            Value for native ``$operator`` parameter.
        value : xs:anyAtomicType*
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:range-query``.
        """
        return _FunctionCall(
            "cts:range-query",
            (index, _operator(operator), value),
            (options, _weight(weight)),
        )

    @staticmethod
    def rank(arg, value, *, options=None) -> Expr:
        """Build a composable ``cts:rank`` call.

        Returns the rank of a value in a data set.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            Value for native ``$arg`` parameter.
        value : xs:anyAtomicType
            Value for native ``$value`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:rank``.
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
            Value for native ``$reference`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:reference-parse``.
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
            Value for native ``$query`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:register``.
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
            Value for native ``$ids`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:registered-query``.
        """
        return _FunctionCall(
            "cts:registered-query",
            (ids,),
            (options, _weight(weight)),
        )

    @staticmethod
    def relevance_info(*, node=None, output_kind=None) -> Expr:
        """Build a composable ``cts:relevance-info`` call.

        Return the relevance score computation report for a node.

        Parameters
        ----------
        node : node()
            Value for native ``$node`` parameter.
        output_kind : xs:string
            Value for native ``$output-kind`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:relevance-info``.
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
            Value for native ``$node`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:remainder``.
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
            Value for native ``$nodes`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:reverse-query``.
        """
        return _FunctionCall(
            "cts:reverse-query",
            (nodes,),
            (_weight(weight),),
        )

    @staticmethod
    def score(*, node=None) -> Expr:
        """Build a composable ``cts:score`` call.

        Returns the score of a node, or of the context node if no node is
        provided.

        Parameters
        ----------
        node : node()
            Value for native ``$node`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:score``.
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
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:score-order``.
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
            Value for native ``$expression`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        options : (cts:order|xs:string)*
            Value for native ``$options`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:search``.
        """
        return _FunctionCall(
            "cts:search",
            (xpath("/") if expression is None else search_path(expression), query),
            (options, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def similar_query(nodes, *, weight=None, options=None) -> Expr:
        """Build a composable ``cts:similar-query`` call.

        Returns a query matching nodes similar to the model nodes.

        Parameters
        ----------
        nodes : node()*
            Value for native ``$nodes`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.
        options : element()?
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:similar-query``.
        """
        return _FunctionCall(
            "cts:similar-query",
            (nodes,),
            (_weight(weight), options),
        )

    @staticmethod
    def stddev(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:stddev`` call.

        Returns a frequency-weighted sample standard deviation given a value
        lexicon.

        Parameters
        ----------
        range_index : cts:reference
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:stddev``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:stddev-p``.
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
            Value for native ``$text`` parameter.
        language : xs:string?
            Value for native ``$language`` parameter.
        part_of_speech : xs:string?
            Value for native ``$partOfSpeech`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:stem``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:sum-aggregate``.
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
            Value for native ``$computed-labels`` parameter.
        known_labels : element(cts:label)*
            Value for native ``$known-labels`` parameter.
        recall_weight : xs:double?
            Value for native ``$recall-weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:thresholds``.
        """
        return _FunctionCall(
            "cts:thresholds",
            (computed_labels, known_labels),
            (_weight(recall_weight),),
        )

    @staticmethod
    def tokenize(text, *, language=None, field=None) -> Expr:
        """Build a composable ``cts:tokenize`` call.

        Tokenizes text into words, punctuation, and spaces.

        Parameters
        ----------
        text : xs:string
            Value for native ``$text`` parameter.
        language : xs:string?
            Value for native ``$language`` parameter.
        field : xs:string?
            Value for native ``$field`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:tokenize``.
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
            Value for native ``$training-nodes`` parameter.
        labels : element(cts:label)*
            Value for native ``$labels`` parameter.
        options : (element()|map:map)?
            Value for native ``$options`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:train``.
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
            Value for native ``$subject`` parameter.
        predicate : xs:anyAtomicType*
            Value for native ``$predicate`` parameter.
        object : xs:anyAtomicType*
            Value for native ``$object`` parameter.
        operator : xs:string*
            Value for native ``$operator`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:triple-range-query``.
        """
        return _FunctionCall(
            "cts:triple-range-query",
            (subject, predicate, object),
            (
                _operator(operator) if operator is not None else None,
                options,
                _weight(weight),
            ),
        )

    @staticmethod
    def triple_value_statistics(*, values=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:triple-value-statistics`` call.

        Returns statistics from the triple index for the values given.

        Parameters
        ----------
        values : xs:anyAtomicType*
            Value for native ``$values`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:triple-value-statistics``.
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
            Value for native ``$subject`` parameter.
        predicate : xs:anyAtomicType*
            Value for native ``$predicate`` parameter.
        object : xs:anyAtomicType*
            Value for native ``$object`` parameter.
        operator : xs:string*
            Value for native ``$operator`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:triples``.
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
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:uri-match``.
        """
        return _FunctionCall(
            "cts:uri-match",
            (pattern,),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:uris``.
        """
        return _FunctionCall(
            "cts:uris",
            (),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def valid_document_patch_path(string, *, map=None) -> Expr:
        """Build a composable ``cts:valid-document-patch-path`` call.

        Parses path expressions and resolves namespaces using the $map
        parameter.

        Parameters
        ----------
        string : xs:string
            Value for native ``$string`` parameter.
        map : map:map?
            Value for native ``$map`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-document-patch-path``.
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
            Value for native ``$string`` parameter.
        map : map:map?
            Value for native ``$map`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-extract-path``.
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
            Value for native ``$string`` parameter.
        ignorens : xs:boolean
            Value for native ``$ignorens`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-index-path``.
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
            Value for native ``$string`` parameter.
        map : map:map?
            Value for native ``$map`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-optic-path``.
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
            Value for native ``$string`` parameter.
        map : map:map?
            Value for native ``$map`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:valid-tde-context``.
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
            Value for native ``$range-index-1`` parameter.
        range_index_2 : cts:reference
            Value for native ``$range-index-2`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:value-co-occurrences``.
        """
        return _FunctionCall(
            "cts:value-co-occurrences",
            (range_index_1, range_index_2),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$range-indexes`` parameter.
        pattern : xs:anyAtomicType
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:value-match``.
        """
        return _FunctionCall(
            "cts:value-match",
            (range_indexes, pattern),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$range-indexes`` parameter.
        bounds : xs:anyAtomicType*
            Value for native ``$bounds`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:value-ranges``.
        """
        return _FunctionCall(
            "cts:value-ranges",
            (range_indexes,),
            (bounds, options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$range-indexes`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:value-tuples``.
        """
        return _FunctionCall(
            "cts:value-tuples",
            (range_indexes,),
            (options, query, _weight(quality_weight), forest_ids),
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
            Value for native ``$range-indexes`` parameter.
        start : xs:anyAtomicType?
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:values``.
        """
        return _FunctionCall(
            "cts:values",
            (range_indexes,),
            (start, options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def variance(range_index, *, options=None, query=None, forest_ids=None) -> Expr:
        """Build a composable ``cts:variance`` call.

        Returns a frequency-weighted sample variance given a value lexicon.

        Parameters
        ----------
        range_index : cts:reference
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:variance``.
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
            Value for native ``$range-index`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:variance-p``.
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
            Value for native ``$node`` parameter.
        query : cts:query
            Value for native ``$query`` parameter.
        expr : item()*
            Value for native ``$expr`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:walk``.
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
            Value for native ``$pattern`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:word-match``.
        """
        return _FunctionCall(
            "cts:word-match",
            (pattern,),
            (options, query, _weight(quality_weight), forest_ids),
        )

    @staticmethod
    def word_query(text, *, options=None, weight=None) -> Expr:
        """Build a composable ``cts:word-query`` call.

        Returns a query matching text content containing a given phrase.

        Parameters
        ----------
        text : xs:string*
            Value for native ``$text`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        weight : xs:double?
            Value for native ``$weight`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:word-query``.
        """
        return _FunctionCall(
            "cts:word-query",
            (text,),
            (options, _weight(weight)),
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
            Value for native ``$start`` parameter.
        options : xs:string*
            Value for native ``$options`` parameter.
        query : cts:query?
            Value for native ``$query`` parameter.
        quality_weight : xs:double?
            Value for native ``$quality-weight`` parameter.
        forest_ids : xs:unsignedLong*
            Value for native ``$forest-ids`` parameter.

        Returns
        -------
        Expr
            Composable call to ``cts:words``.
        """
        return _FunctionCall(
            "cts:words",
            (),
            (start, options, query, _weight(quality_weight), forest_ids),
        )
