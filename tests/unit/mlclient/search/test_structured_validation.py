"""Structured components reject arguments they cannot serialize when built."""

from datetime import datetime

import pytest

from mlclient.search.structured import (
    Circle,
    CollectionQuery,
    Element,
    GeoElementQuery,
    GeoRegionConstraintQuery,
    GeoRegionPathQuery,
    JsonProperty,
    LsqtQuery,
    NearQuery,
    PathIndex,
    Period,
    PeriodCompareQuery,
    PeriodRangeQuery,
    Point,
    Polygon,
    QtextQuery,
    TermQuery,
    ValueQuery,
)


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (lambda: TermQuery(None), "TermQuery.text is required"),
        (lambda: Point(None, 20), "Point.latitude is required"),
        (lambda: Period("2026-01-01T00:00:00Z", None), "Period.end is required"),
        (
            lambda: ValueQuery(JsonProperty("count"), None),
            "ValueQuery.text is required",
        ),
    ],
)
def test_missing_required_arguments_are_rejected(build, message):
    with pytest.raises(TypeError) as error:
        build()

    assert str(error.value) == message


def test_a_set_is_rejected_instead_of_written_as_text():
    with pytest.raises(TypeError) as error:
        CollectionQuery({"a"})

    assert str(error.value) == (
        "CollectionQuery.uris must be a value or a sequence, got set"
    )


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (lambda: QtextQuery(5), "QtextQuery.text must be str, got int"),
        (lambda: Element(5), "Element.name must be str, got int"),
        (lambda: TermQuery(["blue", 5]), "TermQuery.text items must be str, got int"),
        (lambda: Point("10", 20), "Point.latitude must be a number, got str"),
        (
            lambda: TermQuery("blue", weight=True),
            "TermQuery.weight must be a number, got bool",
        ),
        (
            lambda: NearQuery([TermQuery("a")], distance=1.5),
            "NearQuery.distance must be an integer, got float",
        ),
        (lambda: Circle(5, (10, 20)), "Circle.center must be Point, got tuple"),
        (
            lambda: Polygon([(1, 2), (3, 4), (1, 2)]),
            "Polygon.points items must be Point, got tuple",
        ),
        (
            lambda: GeoElementQuery("location", Point(10, 20)),
            "GeoElementQuery.element must be Element, got str",
        ),
        (
            lambda: GeoRegionPathQuery("/region", Point(10, 20)),
            "GeoRegionPathQuery.path must be PathIndex, got str",
        ),
        (
            lambda: PeriodRangeQuery("valid", "aln_equals", "2024"),
            "PeriodRangeQuery.periods items must be Period, got str",
        ),
        (
            lambda: Period(datetime(2026, 1, 1), 2027),
            "Period.end must be datetime or str, got int",
        ),
        (lambda: LsqtQuery(5), "LsqtQuery.temporal_collection must be str, got int"),
    ],
)
def test_arguments_of_unsupported_types_are_rejected(build, message):
    with pytest.raises(TypeError) as error:
        build()

    assert str(error.value) == message


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: PeriodCompareQuery("system", "bogus", "valid"),
            "PeriodCompareQuery.operator 'bogus' is not a temporal operator",
        ),
        (
            lambda: PeriodRangeQuery(
                "valid",
                "bogus",
                Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
            ),
            "PeriodRangeQuery.operator 'bogus' is not a temporal operator",
        ),
        (
            lambda: GeoRegionPathQuery(
                PathIndex("/region"),
                Point(10, 20),
                operator="bogus",
            ),
            "GeoRegionPathQuery.operator 'bogus' is not a geospatial operator",
        ),
        (
            lambda: GeoRegionConstraintQuery("region", Point(10, 20), operator="bogus"),
            "GeoRegionConstraintQuery.operator 'bogus' is not a geospatial operator",
        ),
    ],
)
def test_operators_outside_their_native_set_are_rejected(build, message):
    with pytest.raises(ValueError, match="is not a") as error:
        build()

    assert str(error.value) == message


def test_native_operators_are_accepted():
    PeriodCompareQuery("system", "iso_equals", "valid")
    GeoRegionPathQuery(PathIndex("/region"), Point(10, 20), operator="covered-by")
