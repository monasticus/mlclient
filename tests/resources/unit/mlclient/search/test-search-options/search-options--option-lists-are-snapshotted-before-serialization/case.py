"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


@pytest.mark.parametrize(
    ("build", "member", "option_name"),
    [
        (
            lambda values: SearchOptions().values("price", PRICE, options=values),
            "values",
            "values-option",
        ),
        (
            lambda values: SearchOptions().range_constraint(
                "price",
                PRICE,
                options=values,
            ),
            "range",
            "facet-option",
        ),
        (
            lambda values: SearchOptions().word_constraint(
                "price",
                Element("price"),
                options=values,
            ),
            "word",
            "term-option",
        ),
        (
            lambda values: SearchOptions().value_constraint(
                "price",
                Element("price"),
                options=values,
            ),
            "value",
            "term-option",
        ),
    ],
)
def run(build, member, option_name):
    values = ["first"]
    options = build(values)
    values.append("later")
    result = options.to_json()["options"]
    definition = (
        result["values"][0] if member == "values" else result["constraint"][0][member]
    )
    assert definition[option_name] == read_query_expectation(
        __file__,
        "expected-1.json",
    )
    definition[option_name].append("changed output")
    assert "changed output" not in str(options.to_json())
    xml = tostring(options.to_xml(), encoding="unicode")
    assert "first" in xml
    assert "later" not in xml
    assert "changed output" not in xml
    empty = build([]).to_json()["options"]
    definition = (
        empty["values"][0] if member == "values" else empty["constraint"][0][member]
    )
    assert definition[option_name] == read_query_expectation(
        __file__,
        "expected-2.json",
    )
