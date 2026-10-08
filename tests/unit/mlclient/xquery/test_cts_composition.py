"""CTS queries compose with &, | and ~ and show their arguments in repr."""

import datetime

import pytest

from mlclient.xquery import AndQuery, NotQuery, OrQuery, cts, fn

coffee = cts.word_query("coffee")
tea = cts.word_query("tea")
milk = cts.word_query("milk")


def test_and_operator_builds_an_and_query():
    assert coffee & tea == cts.and_query([coffee, tea])


def test_chained_and_operators_build_one_flat_and_query():
    assert coffee & tea & milk == cts.and_query([coffee, tea, milk])


def test_and_operator_keeps_an_ordered_and_query_as_one_operand():
    ordered = cts.and_query([coffee, tea], options="ordered")

    assert ordered & milk == cts.and_query([ordered, milk])


def test_or_operator_builds_one_flat_or_query():
    assert coffee | tea | milk == cts.or_query([coffee, tea, milk])


def test_invert_operator_builds_a_not_query():
    assert ~coffee == cts.not_query(coffee)
    assert isinstance(~coffee, NotQuery)


def test_operators_combine_into_native_xquery():
    query = (coffee | tea) & ~milk

    assert isinstance(query, AndQuery)
    assert isinstance(query.queries.items[0], OrQuery)
    assert query.to_json() == {
        "andQuery": {
            "queries": [
                {
                    "orQuery": {
                        "queries": [
                            {"wordQuery": {"text": ["coffee"]}},
                            {"wordQuery": {"text": ["tea"]}},
                        ],
                    },
                },
                {"notQuery": {"query": {"wordQuery": {"text": ["milk"]}}}},
            ],
        },
    }


@pytest.mark.parametrize("other", ["tea", 1, None])
def test_operators_reject_non_queries(other):
    with pytest.raises(TypeError):
        coffee & other
    with pytest.raises(TypeError):
        coffee | other


@pytest.mark.parametrize(
    ("query", "text"),
    [
        (cts.word_query("a", weight=2), "WordQuery(text='a', weight=2)"),
        (
            cts.element_range_query(fn.qname("urn:x", "p"), ">=", 10),
            "ElementRangeQuery(element_name=fn:QName('urn:x', 'p'), "
            "operator='>=', value=10)",
        ),
        (
            cts.and_query([cts.word_query("a"), "b"]),
            "AndQuery(queries=[WordQuery(text='a'), 'b'])",
        ),
        (cts.point(10, 20), "Point(latitude_or_wkt=10, longitude=20)"),
        (
            cts.json_property_value_query("active", True),
            "JsonPropertyValueQuery(property_name='active', value=True)",
        ),
        (
            cts.element_query("p", cts.true_query()),
            "ElementQuery(element_name='p', query=TrueQuery())",
        ),
    ],
)
def test_repr_shows_the_supplied_arguments(query, text):
    assert repr(query) == text


def test_repr_shows_other_typed_values_with_their_type():
    query = cts.element_range_query("day", ">", datetime.date(2026, 1, 1))

    assert repr(query) == (
        "ElementRangeQuery(element_name='day', operator='>', "
        "value=xs:date('2026-01-01'))"
    )
