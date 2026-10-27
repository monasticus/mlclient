"""Options constructor aliases compose immutable model components."""

from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import tostring

import pytest

from mlclient.search import opt, options
from mlclient.search.options import Range
from mlclient.search.structured import Attribute, Element, JsonProperty

PRICE_RANGE = Range(Element("price"), "xs:decimal")
SEARCH_NAMESPACE = "http://marklogic.com/appservices/search"
NATIVE_ELEMENT = XmlElement(f"{{{SEARCH_NAMESPACE}}}return-metrics")
NATIVE_ELEMENT.text = "false"


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        pytest.param(
            lambda b: b.options(),
            options.SearchOptions(),
            id="empty-options",
        ),
        pytest.param(
            lambda b: b.options(options.PageLength(20)),
            options.SearchOptions(options.PageLength(20)),
            id="options",
        ),
        pytest.param(
            lambda b: b.range_(Element("title")),
            Range(Element("title")),
            id="range-defaults",
        ),
        pytest.param(
            lambda b: b.range_(
                Element("item"),
                "xs:string",
                collation="http://marklogic.com/collation/",
                attribute=Attribute("code"),
            ),
            Range(
                Element("item"),
                "xs:string",
                collation="http://marklogic.com/collation/",
                attribute=Attribute("code"),
            ),
            id="range-with-options",
        ),
        pytest.param(
            lambda b: b.values("price", PRICE_RANGE),
            options.Values("price", PRICE_RANGE),
            id="values-defaults",
        ),
        pytest.param(
            lambda b: b.values("price", PRICE_RANGE, options=["frequency-order"]),
            options.Values("price", PRICE_RANGE, options=["frequency-order"]),
            id="values-with-options",
        ),
        pytest.param(
            lambda b: b.tuples("pair", PRICE_RANGE, PRICE_RANGE),
            options.Tuples("pair", PRICE_RANGE, PRICE_RANGE),
            id="tuples",
        ),
        pytest.param(
            lambda b: b.range_constraint("price", PRICE_RANGE),
            options.RangeConstraint("price", PRICE_RANGE),
            id="range-constraint-defaults",
        ),
        pytest.param(
            lambda b: b.range_constraint(
                "price",
                PRICE_RANGE,
                facet=False,
                options=["limit=5"],
            ),
            options.RangeConstraint(
                "price",
                PRICE_RANGE,
                facet=False,
                options=["limit=5"],
            ),
            id="range-constraint-with-options",
        ),
        pytest.param(
            lambda b: b.word_constraint("title", Element("title")),
            options.WordConstraint("title", Element("title")),
            id="word-constraint-defaults",
        ),
        pytest.param(
            lambda b: b.word_constraint(
                "code",
                Element("item"),
                attribute=Attribute("code"),
                options="case-sensitive",
            ),
            options.WordConstraint(
                "code",
                Element("item"),
                attribute=Attribute("code"),
                options="case-sensitive",
            ),
            id="word-constraint-with-options",
        ),
        pytest.param(
            lambda b: b.value_constraint("title", Element("title")),
            options.ValueConstraint("title", Element("title")),
            id="value-constraint-defaults",
        ),
        pytest.param(
            lambda b: b.value_constraint(
                "code",
                Element("item"),
                attribute=Attribute("code"),
                options=["exact"],
            ),
            options.ValueConstraint(
                "code",
                Element("item"),
                attribute=Attribute("code"),
                options=["exact"],
            ),
            id="value-constraint-attribute",
        ),
        pytest.param(
            lambda b: b.value_constraint(
                "price",
                JsonProperty("price"),
                node_type="number",
            ),
            options.ValueConstraint("price", JsonProperty("price"), node_type="number"),
            id="value-constraint-node-type",
        ),
        pytest.param(
            lambda b: b.collection_constraint("category"),
            options.CollectionConstraint("category"),
            id="collection-constraint-defaults",
        ),
        pytest.param(
            lambda b: b.collection_constraint(
                "category",
                prefix="/categories/",
                facet=False,
            ),
            options.CollectionConstraint(
                "category",
                prefix="/categories/",
                facet=False,
            ),
            id="collection-constraint-with-options",
        ),
        pytest.param(
            lambda b: b.container_constraint("item", Element("item")),
            options.ContainerConstraint("item", Element("item")),
            id="container-constraint",
        ),
        pytest.param(
            lambda b: b.sort(PRICE_RANGE),
            options.SortOrder(PRICE_RANGE),
            id="sort-defaults",
        ),
        pytest.param(
            lambda b: b.sort(PRICE_RANGE, direction="descending"),
            options.SortOrder(PRICE_RANGE, direction="descending"),
            id="sort-descending",
        ),
        pytest.param(
            lambda b: b.control("return-metrics", False),
            options.Control("return-metrics", False),
            id="control",
        ),
        pytest.param(
            lambda b: b.native({"return-metrics": False}, NATIVE_ELEMENT),
            options.NativeOptions({"return-metrics": False}, NATIVE_ELEMENT),
            id="native",
        ),
        pytest.param(
            lambda b: b.page_length(20),
            options.PageLength(20),
            id="page-length",
        ),
        pytest.param(
            lambda b: b.return_facets(False),
            options.ReturnFacets(False),
            id="return-facets",
        ),
    ],
)
def test_opt_factories_preserve_constructor_arguments(build, expected):
    assert build(opt) == expected


def test_opt_composes_reusable_option_groups():
    defaults = opt.options(
        opt.word_constraint("title", Element("title")),
        opt.page_length(10),
    )
    assert opt.options(
        defaults,
        opt.page_length(20),
        opt.return_facets(False),
    ) == options.SearchOptions(
        options.WordConstraint("title", Element("title")),
        options.PageLength(20),
        options.ReturnFacets(False),
    )


def test_opt_rejects_invalid_page_length():
    with pytest.raises(ValueError, match="page length must be positive") as error:
        opt.page_length(0)
    assert str(error.value) == "page length must be positive"


@pytest.mark.parametrize(
    ("alias", "model"),
    [
        (opt.additional_query, options.AdditionalQuery),
        (opt.aggregate, options.Aggregate),
        (opt.anchor, options.Anchor),
        (opt.annotation, options.Annotation),
        (opt.bucket, options.Bucket),
        (opt.callback, options.Callback),
        (opt.collection, options.Collection),
        (opt.collection_constraint, options.CollectionConstraint),
        (opt.computed_bucket, options.ComputedBucket),
        (opt.concurrency_level, options.ConcurrencyLevel),
        (opt.constraint_value, options.ConstraintValue),
        (opt.container_constraint, options.ContainerConstraint),
        (opt.control, options.Control),
        (opt.custom_constraint, options.CustomConstraint),
        (opt.debug, options.Debug),
        (opt.default_suggestion_source, options.DefaultSuggestionSource),
        (opt.element_query_constraint, options.ElementQueryConstraint),
        (opt.extract_document_data, options.ExtractDocumentData),
        (opt.extract_metadata, options.ExtractMetadata),
        (opt.forest, options.Forest),
        (opt.fragment_scope, options.FragmentScope),
        (opt.geo_attribute_pair, options.GeoAttributePair),
        (opt.geo_constraint, options.GeoConstraint),
        (opt.geo_element, options.GeoElement),
        (opt.geo_element_pair, options.GeoElementPair),
        (opt.geo_json_property, options.GeoJsonProperty),
        (opt.geo_json_property_pair, options.GeoJsonPropertyPair),
        (opt.geo_path, options.GeoPath),
        (opt.geo_region_path, options.GeoRegionPath),
        (opt.grammar, options.Grammar),
        (opt.heatmap, options.Heatmap),
        (opt.implicit, options.Implicit),
        (opt.joiner, options.Joiner),
        (opt.metadata_qname, options.MetadataQName),
        (opt.native, options.NativeOptions),
        (opt.native_option, options.NativeOption),
        (opt.operator, options.Operator),
        (opt.operator_state, options.OperatorState),
        (opt.options, options.SearchOptions),
        (opt.page_length, options.PageLength),
        (opt.preferred_matches, options.PreferredMatches),
        (opt.properties_constraint, options.PropertiesConstraint),
        (opt.quality_weight, options.QualityWeight),
        (opt.range_, options.Range),
        (opt.range_constraint, options.RangeConstraint),
        (opt.result_decorator, options.ResultDecorator),
        (opt.return_aggregates, options.ReturnAggregates),
        (opt.return_constraints, options.ReturnConstraints),
        (opt.return_facets, options.ReturnFacets),
        (opt.return_frequencies, options.ReturnFrequencies),
        (opt.return_metrics, options.ReturnMetrics),
        (opt.return_plan, options.ReturnPlan),
        (opt.return_qtext, options.ReturnQtext),
        (opt.return_query, options.ReturnQuery),
        (opt.return_results, options.ReturnResults),
        (opt.return_similar, options.ReturnSimilar),
        (opt.return_values, options.ReturnValues),
        (opt.search_option, options.SearchOptionString),
        (opt.searchable_expression, options.SearchableExpression),
        (opt.sort, options.SortOrder),
        (opt.starter, options.Starter),
        (opt.suggestion_source, options.SuggestionSource),
        (opt.term, options.Term),
        (opt.term_default, options.TermDefault),
        (opt.transform_results, options.TransformResults),
        (opt.tuples, options.Tuples),
        (opt.value, options.Value),
        (opt.value_constraint, options.ValueConstraint),
        (opt.values, options.Values),
        (opt.word, options.Word),
        (opt.word_constraint, options.WordConstraint),
        (opt.word_lexicon, options.WordLexicon),
    ],
)
def test_constructor_alias_is_the_model(alias, model):
    assert alias is model


def test_nested_constructor_aliases_define_facets_snippets_and_operator_states():
    actual = opt.options(
        opt.range_constraint(
            "price",
            opt.range_(
                JsonProperty("price"),
                "xs:decimal",
                buckets=[opt.bucket("low", "Under ten", lt="10")],
            ),
        ),
        opt.transform_results(
            preferred_matches=opt.preferred_matches([JsonProperty("title")]),
            max_matches=2,
        ),
        opt.operator(
            "sort",
            [
                opt.operator_state(
                    "relevance",
                    opt.options(opt.sort("score", direction="descending")),
                ),
            ],
        ),
    )
    expected = options.SearchOptions(
        options.RangeConstraint(
            "price",
            options.Range(
                JsonProperty("price"),
                "xs:decimal",
                buckets=[options.Bucket("low", "Under ten", lt="10")],
            ),
        ),
        options.TransformResults(
            preferred_matches=options.PreferredMatches([JsonProperty("title")]),
            max_matches=2,
        ),
        options.Operator(
            "sort",
            [
                options.OperatorState(
                    "relevance",
                    options.SearchOptions(
                        options.SortOrder("score", direction="descending"),
                    ),
                ),
            ],
        ),
    )
    assert actual.to_json() == expected.to_json()
    assert tostring(actual.to_xml()) == tostring(expected.to_xml())
