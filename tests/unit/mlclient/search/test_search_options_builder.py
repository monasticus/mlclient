"""The options builder constructs the same models as their public constructors."""

from xml.etree.ElementTree import Element as XmlElement

import pytest

from mlclient.search import options
from mlclient.search.options import Range, SearchOptionsBuilder, opt
from mlclient.search.structured import Attribute, Element, JsonProperty

PRICE_RANGE = Range(Element("price"), "xs:decimal")
SEARCH_NAMESPACE = "http://marklogic.com/appservices/search"
NATIVE_ELEMENT = XmlElement(f"{{{SEARCH_NAMESPACE}}}return-metrics")
NATIVE_ELEMENT.text = "false"


@pytest.mark.parametrize(
    "builder",
    [opt, SearchOptionsBuilder()],
    ids=["opt", "instance"],
)
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
            lambda b: b.range(Element("title")),
            Range(Element("title")),
            id="range-defaults",
        ),
        pytest.param(
            lambda b: b.range(
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
def test_builder_factories_preserve_constructor_arguments(builder, build, expected):
    assert build(builder) == expected


def test_builder_composes_reusable_option_groups():
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


def test_builder_rejects_invalid_page_length():
    with pytest.raises(ValueError, match="page length must be positive") as error:
        opt.page_length(0)
    assert str(error.value) == "page length must be positive"
