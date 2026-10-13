"""Structured queries compose with &, | and ~."""

import pytest

from mlclient.search.structured import AndQuery, NotQuery, OrQuery, Query, TermQuery

blue = TermQuery("blue")
green = TermQuery("green")
red = TermQuery("red")


def test_and_operator_builds_one_flat_and_query():
    assert blue & green & red == AndQuery((blue, green, red))


def test_and_operator_keeps_an_ordered_and_query_as_one_operand():
    ordered = AndQuery((blue, green), ordered=True)

    assert ordered & red == AndQuery((ordered, red))


def test_or_operator_builds_one_flat_or_query():
    assert blue | green | red == OrQuery((blue, green, red))


def test_invert_operator_builds_a_not_query():
    assert ~blue == NotQuery(blue)


def test_operators_combine():
    assert (blue | green) & ~red == AndQuery((OrQuery((blue, green)), NotQuery(red)))


@pytest.mark.parametrize("other", ["green", None])
def test_operators_reject_non_queries(other):
    with pytest.raises(TypeError):
        blue & other
    with pytest.raises(TypeError):
        blue | other


def test_operators_reject_the_query_wrapper():
    with pytest.raises(TypeError, match="not Query wrappers"):
        blue & Query(green)
