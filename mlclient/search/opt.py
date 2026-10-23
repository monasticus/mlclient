"""Short constructor aliases for immutable Search API options and nested components."""

from __future__ import annotations

from mlclient.search.options import (
    AdditionalQuery,
    Aggregate,
    Anchor,
    Annotation,
    Bucket,
    Callback,
    Collection,
    CollectionConstraint,
    ComputedBucket,
    ConcurrencyLevel,
    ConstraintValue,
    ContainerConstraint,
    Control,
    CustomConstraint,
    Debug,
    DefaultSuggestionSource,
    ElementQueryConstraint,
    ExtractDocumentData,
    ExtractMetadata,
    Forest,
    FragmentScope,
    GeoAttributePair,
    GeoConstraint,
    GeoElement,
    GeoElementPair,
    GeoJsonProperty,
    GeoJsonPropertyPair,
    GeoPath,
    GeoRegionPath,
    Grammar,
    Heatmap,
    Implicit,
    Joiner,
    MetadataQName,
    NativeOption,
    NativeOptions,
    Operator,
    OperatorState,
    PageLength,
    PreferredMatches,
    PropertiesConstraint,
    QualityWeight,
    Range,
    RangeConstraint,
    ResultDecorator,
    ReturnAggregates,
    ReturnConstraints,
    ReturnFacets,
    ReturnFrequencies,
    ReturnMetrics,
    ReturnPlan,
    ReturnQtext,
    ReturnQuery,
    ReturnResults,
    ReturnSimilar,
    ReturnValues,
    SearchableExpression,
    SearchOptions,
    SearchOptionString,
    SortOrder,
    Starter,
    SuggestionSource,
    Term,
    TermDefault,
    TransformResults,
    Tuples,
    Value,
    ValueConstraint,
    Values,
    Word,
    WordConstraint,
    WordLexicon,
)

__all__ = [
    "additional_query",
    "aggregate",
    "anchor",
    "annotation",
    "bucket",
    "callback",
    "collection",
    "collection_constraint",
    "computed_bucket",
    "concurrency_level",
    "constraint_value",
    "container_constraint",
    "control",
    "custom_constraint",
    "debug",
    "default_suggestion_source",
    "element_query_constraint",
    "extract_document_data",
    "extract_metadata",
    "forest",
    "fragment_scope",
    "geo_attribute_pair",
    "geo_constraint",
    "geo_element",
    "geo_element_pair",
    "geo_json_property",
    "geo_json_property_pair",
    "geo_path",
    "geo_region_path",
    "grammar",
    "heatmap",
    "implicit",
    "joiner",
    "metadata_qname",
    "native",
    "native_option",
    "operator",
    "operator_state",
    "options",
    "page_length",
    "preferred_matches",
    "properties_constraint",
    "quality_weight",
    "range_",
    "range_constraint",
    "result_decorator",
    "return_aggregates",
    "return_constraints",
    "return_facets",
    "return_frequencies",
    "return_metrics",
    "return_plan",
    "return_qtext",
    "return_query",
    "return_results",
    "return_similar",
    "return_values",
    "search_option",
    "searchable_expression",
    "sort",
    "starter",
    "suggestion_source",
    "term",
    "term_default",
    "transform_results",
    "tuples",
    "value",
    "value_constraint",
    "values",
    "word",
    "word_constraint",
    "word_lexicon",
]

additional_query = AdditionalQuery
aggregate = Aggregate
anchor = Anchor
annotation = Annotation
bucket = Bucket
callback = Callback
collection = Collection
collection_constraint = CollectionConstraint
computed_bucket = ComputedBucket
concurrency_level = ConcurrencyLevel
constraint_value = ConstraintValue
container_constraint = ContainerConstraint
control = Control
custom_constraint = CustomConstraint
debug = Debug
default_suggestion_source = DefaultSuggestionSource
element_query_constraint = ElementQueryConstraint
extract_document_data = ExtractDocumentData
extract_metadata = ExtractMetadata
forest = Forest
fragment_scope = FragmentScope
geo_attribute_pair = GeoAttributePair
geo_constraint = GeoConstraint
geo_element = GeoElement
geo_element_pair = GeoElementPair
geo_json_property = GeoJsonProperty
geo_json_property_pair = GeoJsonPropertyPair
geo_path = GeoPath
geo_region_path = GeoRegionPath
grammar = Grammar
heatmap = Heatmap
implicit = Implicit
joiner = Joiner
metadata_qname = MetadataQName
native = NativeOptions
native_option = NativeOption
operator = Operator
operator_state = OperatorState
options = SearchOptions
page_length = PageLength
preferred_matches = PreferredMatches
properties_constraint = PropertiesConstraint
quality_weight = QualityWeight
range_ = Range
range_constraint = RangeConstraint
result_decorator = ResultDecorator
return_aggregates = ReturnAggregates
return_constraints = ReturnConstraints
return_facets = ReturnFacets
return_frequencies = ReturnFrequencies
return_metrics = ReturnMetrics
return_plan = ReturnPlan
return_qtext = ReturnQtext
return_query = ReturnQuery
return_results = ReturnResults
return_similar = ReturnSimilar
return_values = ReturnValues
search_option = SearchOptionString
searchable_expression = SearchableExpression
sort = SortOrder
starter = Starter
suggestion_source = SuggestionSource
term = Term
term_default = TermDefault
transform_results = TransformResults
tuples = Tuples
value = Value
value_constraint = ValueConstraint
values = Values
word = Word
word_constraint = WordConstraint
word_lexicon = WordLexicon
