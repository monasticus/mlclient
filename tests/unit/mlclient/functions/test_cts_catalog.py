"""Contract coverage for the supported MarkLogic 12 CTS catalog."""

from __future__ import annotations

import inspect
import re

from mlclient.functions import Cts, fn, xpath


# Generated once from the MarkLogic 12 cts function reference. Keeping this
# inventory explicit makes accidental omissions and accessor creep reviewable.
CTS_SIGNATURES = {
    "after_query": ("cts:after-query", ("timestamp",), ()),
    "aggregate": (
        "cts:aggregate",
        ("native_plugin", "aggregate_name", "range_indexes"),
        ("argument", "options", "query", "forest_ids"),
    ),
    "and_not_query": ("cts:and-not-query", ("positive_query", "negative_query"), ()),
    "and_query": ("cts:and-query", ("queries",), ("options",)),
    "avg_aggregate": (
        "cts:avg-aggregate",
        ("range_index",),
        ("options", "query", "forest_ids"),
    ),
    "before_query": ("cts:before-query", ("timestamp",), ()),
    "boost_query": ("cts:boost-query", ("matching_query", "boosting_query"), ()),
    "box": ("cts:box", ("south", "west", "north", "east"), ()),
    "circle": ("cts:circle", ("radius", "center"), ()),
    "classify": (
        "cts:classify",
        ("data_nodes", "classifier"),
        ("options", "training_nodes"),
    ),
    "cluster": ("cts:cluster", ("nodes",), ("options",)),
    "collection_match": (
        "cts:collection-match",
        ("pattern",),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "collection_query": ("cts:collection-query", ("uris",), ()),
    "collection_reference": ("cts:collection-reference", (), ("options",)),
    "collections": (
        "cts:collections",
        (),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "column_range_query": (
        "cts:column-range-query",
        ("schema", "view", "column", "value"),
        ("operator", "options", "weight"),
    ),
    "complex_polygon": ("cts:complex-polygon", ("outer", "inner"), ()),
    "confidence": ("cts:confidence", (), ("node",)),
    "confidence_order": ("cts:confidence-order", (), ("options",)),
    "contains": ("cts:contains", ("nodes", "query"), ()),
    "correlation": (
        "cts:correlation",
        ("value1", "value2"),
        ("options", "query", "forest_ids"),
    ),
    "count_aggregate": (
        "cts:count-aggregate",
        ("range_index",),
        ("options", "query", "forest_ids"),
    ),
    "covariance": (
        "cts:covariance",
        ("value1", "value2"),
        ("options", "query", "forest_ids"),
    ),
    "covariance_p": (
        "cts:covariance-p",
        ("value1", "value2"),
        ("options", "query", "forest_ids"),
    ),
    "deregister": ("cts:deregister", ("id",), ()),
    "directory_query": ("cts:directory-query", ("uris",), ("depth",)),
    "distinctive_terms": ("cts:distinctive-terms", ("nodes",), ("options",)),
    "document_format_query": ("cts:document-format-query", ("format",), ()),
    "document_fragment_query": ("cts:document-fragment-query", ("query",), ()),
    "document_order": ("cts:document-order", (), ("options",)),
    "document_permission_query": (
        "cts:document-permission-query",
        ("role", "capability"),
        (),
    ),
    "document_query": ("cts:document-query", ("uris",), ()),
    "document_root_query": ("cts:document-root-query", ("root",), ()),
    "element_attribute_pair_geospatial_boxes": (
        "cts:element-attribute-pair-geospatial-boxes",
        ("parent_element_names", "latitude_names", "longitude_names"),
        (
            "latitude_bounds",
            "longitude_bounds",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "element_attribute_pair_geospatial_query": (
        "cts:element-attribute-pair-geospatial-query",
        (
            "element_name",
            "latitude_attribute_names",
            "longitude_attribute_names",
            "regions",
        ),
        ("options", "weight"),
    ),
    "element_attribute_pair_geospatial_value_match": (
        "cts:element-attribute-pair-geospatial-value-match",
        ("element_names", "latitude_names", "longitude_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_pair_geospatial_values": (
        "cts:element-attribute-pair-geospatial-values",
        ("element_names", "latitude_names", "longitude_names"),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_range_query": (
        "cts:element-attribute-range-query",
        ("element_name", "attribute_name", "operator", "value"),
        ("options", "weight"),
    ),
    "element_attribute_reference": (
        "cts:element-attribute-reference",
        ("element", "attribute"),
        ("options",),
    ),
    "element_attribute_value_co_occurrences": (
        "cts:element-attribute-value-co-occurrences",
        ("element_name_1", "attribute_name_1", "element_name_2", "attribute_name_2"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_value_geospatial_co_occurrences": (
        "cts:element-attribute-value-geospatial-co-occurrences",
        ("element_name_1", "attribute_name_1", "geo_element_name"),
        (
            "coord_child_name_1",
            "coord_child_name_2",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "element_attribute_value_match": (
        "cts:element-attribute-value-match",
        ("element_names", "attribute_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_value_query": (
        "cts:element-attribute-value-query",
        ("element_name", "attribute_name", "text"),
        ("options", "weight"),
    ),
    "element_attribute_value_ranges": (
        "cts:element-attribute-value-ranges",
        ("element_names", "attribute_names"),
        ("bounds", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_values": (
        "cts:element-attribute-values",
        ("element_names", "attribute_names"),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_word_match": (
        "cts:element-attribute-word-match",
        ("element_names", "attribute_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_attribute_word_query": (
        "cts:element-attribute-word-query",
        ("element_name", "attribute_name", "text"),
        ("options", "weight"),
    ),
    "element_attribute_words": (
        "cts:element-attribute-words",
        ("element_names", "attribute_names"),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_child_geospatial_boxes": (
        "cts:element-child-geospatial-boxes",
        ("parent_element_names", "child_element_names"),
        (
            "latitude_bounds",
            "longitude_bounds",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "element_child_geospatial_query": (
        "cts:element-child-geospatial-query",
        ("parent_element_name", "child_element_names", "regions"),
        ("options", "weight"),
    ),
    "element_child_geospatial_value_match": (
        "cts:element-child-geospatial-value-match",
        ("element_names", "child_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_child_geospatial_values": (
        "cts:element-child-geospatial-values",
        ("element_names", "child_names"),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_geospatial_boxes": (
        "cts:element-geospatial-boxes",
        ("element_names",),
        (
            "latitude_bounds",
            "longitude_bounds",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "element_geospatial_query": (
        "cts:element-geospatial-query",
        ("element_name", "regions"),
        ("options", "weight"),
    ),
    "element_geospatial_value_match": (
        "cts:element-geospatial-value-match",
        ("element_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_geospatial_values": (
        "cts:element-geospatial-values",
        ("element_names",),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_pair_geospatial_boxes": (
        "cts:element-pair-geospatial-boxes",
        ("parent_element_names", "latitude_names", "longitude_names"),
        (
            "latitude_bounds",
            "longitude_bounds",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "element_pair_geospatial_query": (
        "cts:element-pair-geospatial-query",
        (
            "element_name",
            "latitude_element_names",
            "longitude_element_names",
            "regions",
        ),
        ("options", "weight"),
    ),
    "element_pair_geospatial_value_match": (
        "cts:element-pair-geospatial-value-match",
        ("element_names", "latitude_names", "longitude_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_pair_geospatial_values": (
        "cts:element-pair-geospatial-values",
        ("element_names", "latitude_names", "longitude_names"),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_query": ("cts:element-query", ("element_name", "query"), ()),
    "element_range_query": (
        "cts:element-range-query",
        ("element_name", "operator", "value"),
        ("options", "weight"),
    ),
    "element_reference": ("cts:element-reference", ("element",), ("options",)),
    "element_value_co_occurrences": (
        "cts:element-value-co-occurrences",
        ("element_name_1", "element_name_2"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_value_geospatial_co_occurrences": (
        "cts:element-value-geospatial-co-occurrences",
        ("element_name_1", "geo_element_name"),
        (
            "coord_child_name_1",
            "coord_child_name_2",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "element_value_match": (
        "cts:element-value-match",
        ("element_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_value_query": (
        "cts:element-value-query",
        ("element_name",),
        ("text", "options", "weight"),
    ),
    "element_value_ranges": (
        "cts:element-value-ranges",
        ("element_names",),
        ("bounds", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_values": (
        "cts:element-values",
        ("element_names",),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "element_walk": ("cts:element-walk", ("node", "element", "expr"), ()),
    "element_word_match": (
        "cts:element-word-match",
        ("element_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "element_word_query": (
        "cts:element-word-query",
        ("element_name", "text"),
        ("options", "weight"),
    ),
    "element_words": (
        "cts:element-words",
        ("element_names",),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "entity": ("cts:entity", ("id", "normalized_text", "text", "type"), ()),
    "entity_dictionary": ("cts:entity-dictionary", ("entities",), ("options",)),
    "entity_dictionary_get": ("cts:entity-dictionary-get", ("uri",), ()),
    "entity_dictionary_parse": (
        "cts:entity-dictionary-parse",
        ("contents",),
        ("options",),
    ),
    "entity_highlight": ("cts:entity-highlight", ("node", "expr"), ("dict",)),
    "entity_walk": ("cts:entity-walk", ("node", "expr"), ("dict",)),
    "estimate": (
        "cts:estimate",
        (),
        ("query", "options", "quality_weight", "forest_ids", "maximum"),
    ),
    "false_query": ("cts:false-query", (), ()),
    "field_range_query": (
        "cts:field-range-query",
        ("field_name", "operator", "value"),
        ("options", "weight"),
    ),
    "field_reference": ("cts:field-reference", ("field",), ("options",)),
    "field_value_co_occurrences": (
        "cts:field-value-co-occurrences",
        ("field_name_1", "field_name_2"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "field_value_match": (
        "cts:field-value-match",
        ("field_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "field_value_query": (
        "cts:field-value-query",
        ("field_name", "text"),
        ("options", "weight"),
    ),
    "field_value_ranges": (
        "cts:field-value-ranges",
        ("field_names",),
        ("bounds", "options", "query", "quality_weight", "forest_ids"),
    ),
    "field_values": (
        "cts:field-values",
        ("field_names",),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "field_word_match": (
        "cts:field-word-match",
        ("field_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "field_word_query": (
        "cts:field-word-query",
        ("field_name", "text"),
        ("options", "weight"),
    ),
    "field_words": (
        "cts:field-words",
        ("field_names",),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "fitness": ("cts:fitness", (), ("node",)),
    "fitness_order": ("cts:fitness-order", (), ("options",)),
    "frequency": ("cts:frequency", ("value",), ()),
    "geospatial_attribute_pair_reference": (
        "cts:geospatial-attribute-pair-reference",
        ("element", "lat", "long"),
        ("options",),
    ),
    "geospatial_boxes": (
        "cts:geospatial-boxes",
        ("geo_indexes",),
        (
            "latitude_bounds",
            "longitude_bounds",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "geospatial_co_occurrences": (
        "cts:geospatial-co-occurrences",
        ("geo_element_name_1", "geo_element_name_2"),
        (
            "child_1_name_1",
            "child_1_name_2",
            "child_2_name_1",
            "child_2_name_2",
            "options",
            "query",
            "quality_weight",
            "forest_ids",
        ),
    ),
    "geospatial_element_child_reference": (
        "cts:geospatial-element-child-reference",
        ("element", "child"),
        ("options",),
    ),
    "geospatial_element_pair_reference": (
        "cts:geospatial-element-pair-reference",
        ("element", "lat", "long"),
        ("options",),
    ),
    "geospatial_element_reference": (
        "cts:geospatial-element-reference",
        ("element",),
        ("options",),
    ),
    "geospatial_json_property_child_reference": (
        "cts:geospatial-json-property-child-reference",
        ("property", "child"),
        ("options",),
    ),
    "geospatial_json_property_pair_reference": (
        "cts:geospatial-json-property-pair-reference",
        ("property", "lat", "long"),
        ("options",),
    ),
    "geospatial_json_property_reference": (
        "cts:geospatial-json-property-reference",
        ("property",),
        ("options",),
    ),
    "geospatial_path_reference": (
        "cts:geospatial-path-reference",
        ("path_expression",),
        ("options", "map"),
    ),
    "geospatial_region_path_reference": (
        "cts:geospatial-region-path-reference",
        ("path_expression",),
        ("options", "namespaces", "geohash_precision", "units", "invalid_values"),
    ),
    "geospatial_region_query": (
        "cts:geospatial-region-query",
        ("geospatial_region_reference", "operation", "regions"),
        ("options", "weight"),
    ),
    "highlight": ("cts:highlight", ("node", "query", "expr"), ()),
    "index_order": ("cts:index-order", ("index",), ("options",)),
    "iri_reference": ("cts:iri-reference", (), ()),
    "json_property_child_geospatial_query": (
        "cts:json-property-child-geospatial-query",
        ("parent_property_name", "child_property_names", "regions"),
        ("options", "weight"),
    ),
    "json_property_geospatial_query": (
        "cts:json-property-geospatial-query",
        ("property_name", "regions"),
        ("options", "weight"),
    ),
    "json_property_pair_geospatial_query": (
        "cts:json-property-pair-geospatial-query",
        (
            "property_name",
            "latitude_property_names",
            "longitude_property_names",
            "regions",
        ),
        ("options", "weight"),
    ),
    "json_property_range_query": (
        "cts:json-property-range-query",
        ("property_name", "operator", "value"),
        ("options", "weight"),
    ),
    "json_property_reference": (
        "cts:json-property-reference",
        ("property",),
        ("options",),
    ),
    "json_property_scope_query": (
        "cts:json-property-scope-query",
        ("property_name", "query"),
        (),
    ),
    "json_property_value_query": (
        "cts:json-property-value-query",
        ("property_name", "value"),
        ("options", "weight"),
    ),
    "json_property_word_match": (
        "cts:json-property-word-match",
        ("property_names", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "json_property_word_query": (
        "cts:json-property-word-query",
        ("property_name", "text"),
        ("options", "weight"),
    ),
    "json_property_words": (
        "cts:json-property-words",
        ("property_names",),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
    "linear_model": (
        "cts:linear-model",
        ("values",),
        ("options", "query", "forest_ids"),
    ),
    "linestring": ("cts:linestring", ("vertices",), ()),
    "locks_fragment_query": ("cts:locks-fragment-query", ("query",), ()),
    "lsqt_query": (
        "cts:lsqt-query",
        ("temporal_collection",),
        ("timestamp", "options", "weight"),
    ),
    "match_regions": (
        "cts:match-regions",
        ("range_indexes", "operation", "regions"),
        ("options", "query", "forest_ids"),
    ),
    "max": ("cts:max", ("range_index",), ("options", "query", "forest_ids")),
    "median": ("cts:median", ("arg",), ()),
    "min": ("cts:min", ("range_index",), ("options", "query", "forest_ids")),
    "near_query": (
        "cts:near-query",
        ("queries",),
        ("distance", "options", "distance_weight"),
    ),
    "not_in_query": ("cts:not-in-query", ("positive_query", "negative_query"), ()),
    "not_query": ("cts:not-query", ("query",), ()),
    "or_query": ("cts:or-query", ("queries",), ("options",)),
    "parse": ("cts:parse", ("query",), ("bindings",)),
    "part_of_speech": ("cts:part-of-speech", ("token",), ()),
    "path_geospatial_query": (
        "cts:path-geospatial-query",
        ("path_expression", "regions"),
        ("options", "weight"),
    ),
    "path_range_query": (
        "cts:path-range-query",
        ("path_expression", "operator", "value"),
        ("options", "weight"),
    ),
    "path_reference": (
        "cts:path-reference",
        ("path_expression",),
        ("options", "namespaces"),
    ),
    "percent_rank": ("cts:percent-rank", ("arg", "value"), ("options",)),
    "percentile": ("cts:percentile", ("arg", "p"), ()),
    "period": ("cts:period", ("start", "end"), ()),
    "period_compare": ("cts:period-compare", ("period_1", "operator", "period_2"), ()),
    "period_compare_query": (
        "cts:period-compare-query",
        ("axis_1", "operator", "axis_2"),
        ("options",),
    ),
    "period_range_query": (
        "cts:period-range-query",
        ("axis_name", "operator"),
        ("period", "options"),
    ),
    "point": ("cts:point", ("latitude_or_wkt",), ("longitude",)),
    "polygon": ("cts:polygon", ("vertices",), ()),
    "properties_fragment_query": ("cts:properties-fragment-query", ("query",), ()),
    "quality": ("cts:quality", (), ("node",)),
    "quality_order": ("cts:quality-order", (), ("options",)),
    "query": ("cts:query", ("query",), ()),
    "range_query": (
        "cts:range-query",
        ("index", "operator", "value"),
        ("options", "weight"),
    ),
    "rank": ("cts:rank", ("arg", "value"), ("options",)),
    "reference_parse": ("cts:reference-parse", ("reference",), ()),
    "register": ("cts:register", ("query",), ()),
    "registered_query": ("cts:registered-query", ("ids",), ("options", "weight")),
    "relevance_info": ("cts:relevance-info", (), ("node", "output_kind")),
    "remainder": ("cts:remainder", (), ("node",)),
    "reverse_query": ("cts:reverse-query", ("nodes",), ("weight",)),
    "score": ("cts:score", (), ("node",)),
    "score_order": ("cts:score-order", (), ("options",)),
    "search": (
        "cts:search",
        (),
        ("expression", "query", "options", "quality_weight", "forest_ids"),
    ),
    "similar_query": ("cts:similar-query", ("nodes",), ("weight", "options")),
    "stddev": ("cts:stddev", ("range_index",), ("options", "query", "forest_ids")),
    "stddev_p": ("cts:stddev-p", ("range_index",), ("options", "query", "forest_ids")),
    "stem": ("cts:stem", ("text",), ("language", "part_of_speech")),
    "sum_aggregate": (
        "cts:sum-aggregate",
        ("range_index",),
        ("options", "query", "forest_ids"),
    ),
    "thresholds": (
        "cts:thresholds",
        ("computed_labels", "known_labels"),
        ("recall_weight",),
    ),
    "tokenize": ("cts:tokenize", ("text",), ("language", "field")),
    "train": ("cts:train", ("training_nodes", "labels"), ("options",)),
    "triple_range_query": (
        "cts:triple-range-query",
        ("subject", "predicate", "object"),
        ("operator", "options", "weight"),
    ),
    "triple_value_statistics": (
        "cts:triple-value-statistics",
        (),
        ("values", "forest_ids"),
    ),
    "triples": (
        "cts:triples",
        (),
        (
            "subject",
            "predicate",
            "object",
            "operator",
            "options",
            "query",
            "forest_ids",
        ),
    ),
    "true_query": ("cts:true-query", (), ()),
    "unordered": ("cts:unordered", (), ()),
    "uri_match": (
        "cts:uri-match",
        ("pattern",),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "uri_reference": ("cts:uri-reference", (), ()),
    "uris": (
        "cts:uris",
        (),
        ("query", "start", "options", "quality_weight", "forest_ids"),
    ),
    "valid_document_patch_path": (
        "cts:valid-document-patch-path",
        ("string",),
        ("map",),
    ),
    "valid_extract_path": ("cts:valid-extract-path", ("string",), ("map",)),
    "valid_index_path": ("cts:valid-index-path", ("string", "ignorens"), ()),
    "valid_optic_path": ("cts:valid-optic-path", ("string",), ("map",)),
    "valid_tde_context": ("cts:valid-tde-context", ("string",), ("map",)),
    "value_co_occurrences": (
        "cts:value-co-occurrences",
        ("range_index_1", "range_index_2"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "value_match": (
        "cts:value-match",
        ("range_indexes", "pattern"),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "value_ranges": (
        "cts:value-ranges",
        ("range_indexes",),
        ("bounds", "options", "query", "quality_weight", "forest_ids"),
    ),
    "value_tuples": (
        "cts:value-tuples",
        ("range_indexes",),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "values": (
        "cts:values",
        ("range_indexes",),
        ("query", "start", "options", "quality_weight", "forest_ids"),
    ),
    "variance": ("cts:variance", ("range_index",), ("options", "query", "forest_ids")),
    "variance_p": (
        "cts:variance-p",
        ("range_index",),
        ("options", "query", "forest_ids"),
    ),
    "walk": ("cts:walk", ("node", "query", "expr"), ()),
    "word_match": (
        "cts:word-match",
        ("pattern",),
        ("options", "query", "quality_weight", "forest_ids"),
    ),
    "word_query": ("cts:word-query", ("text",), ("options", "weight")),
    "words": (
        "cts:words",
        (),
        ("start", "options", "query", "quality_weight", "forest_ids"),
    ),
}


def test_cts_catalog_matches_supported_reference_scope():
    public = {name for name in vars(Cts) if not name.startswith("_")}
    assert public == set(CTS_SIGNATURES)


def test_catalog_preserves_native_argument_order_and_every_optional_slot():
    for method_name, (native, required, optional) in CTS_SIGNATURES.items():
        method = getattr(Cts, method_name)
        assert tuple(inspect.signature(method).parameters) == required + optional
        order = required + optional
        if method_name == "geospatial_co_occurrences":
            order = (required[0], *optional[:2], required[1], *optional[2:])
        elif method_name in {"uris", "values"}:
            order = (
                *required,
                "start",
                "options",
                "query",
                "quality_weight",
                "forest_ids",
            )

        # Distinct expressions make swaps, lost arguments and wrong arity visible.
        markers = {name: xpath(f"$arg_{name}") for name in order}
        for supplied in [required, order, *((*required, name) for name in optional)]:
            expr = method(**{name: markers[name] for name in supplied})
            code = expr.compile()[0].splitlines()[-1]
            assert code.startswith(native + "("), method_name
            body = code[len(native) + 1 : -1]
            arguments = body.split(", ") if body else []
            last = max((order.index(name) for name in supplied), default=-1)
            if method_name in {"search", "directory_query"}:
                last = max(last, 1)
            elif method_name == "estimate":
                last = max(last, 0)
            assert len(arguments) == last + 1, (method_name, supplied, code)
            for name, argument in zip(order, arguments):
                expected = [f"$arg_{name}"] if name in supplied else []
                assert re.findall(r"\$arg_\w+", argument) == expected, (
                    method_name,
                    name,
                    code,
                )
            assert fn.count(expr).compile()[0].endswith(f"fn:count({code})")
