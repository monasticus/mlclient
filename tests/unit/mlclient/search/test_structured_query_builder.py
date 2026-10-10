"""The structured builder constructs query objects with the supplied arguments."""

import pytest

from mlclient.search.structured import (
    AndQuery,
    CollectionQuery,
    Element,
    NearQuery,
    NotQuery,
    OrQuery,
    Query,
    RangeQuery,
    StructuredQueryBuilder,
    TermQuery,
    sq,
)


def test_builder_composes_range_and_term():
    query = sq.query(
        sq.and_(
            sq.range(sq.element("price"), 20, operator="GE", index_type="xs:int"),
            sq.term("blue"),
        ),
    )
    assert query == Query(
        [
            AndQuery(
                [
                    RangeQuery(
                        Element("price"), 20, operator="GE", index_type="xs:int",
                    ),
                    TermQuery("blue"),
                ],
            ),
        ],
    )


@pytest.mark.parametrize("ordered", [None, True, False])
def test_builder_and_preserves_order(ordered):
    builder = StructuredQueryBuilder()
    blue = builder.term("blue")
    green = builder.term("green")
    assert builder.and_(blue, green, ordered=ordered) == AndQuery(
        [TermQuery("blue"), TermQuery("green")],
        ordered=ordered,
    )


def test_builder_or_composes_queries():
    assert sq.or_(sq.collection("reports"), sq.not_(sq.term("blue"))) == OrQuery(
        [CollectionQuery("reports"), NotQuery(TermQuery("blue"))],
    )


def test_builder_near_preserves_optional_arguments():
    assert sq.near(
        sq.term("blue"),
        sq.term("green"),
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    ) == NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )


def test_builder_near_without_options():
    assert sq.near(sq.term("blue")) == NearQuery([TermQuery("blue")])


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (sq.query, Query([])),
        (sq.and_, AndQuery([])),
        (sq.or_, OrQuery([])),
        (sq.near, NearQuery([])),
    ],
    ids=["query", "and", "or", "near"],
)
def test_builder_empty_composition(build, expected):
    assert build() == expected


def test_builder_near_rejects_invalid_distance():
    with pytest.raises(TypeError, match=r"NearQuery.distance must be an integer"):
        sq.near(sq.term("blue"), distance=1.5)
