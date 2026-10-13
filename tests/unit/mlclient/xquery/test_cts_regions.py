"""Region and period values built by cts compile natively and expose their text."""

import datetime

import pytest

from mlclient.xquery import Box, Circle, Period, Point, Polygon, cts, xs


@pytest.mark.parametrize(
    ("region", "region_type", "text"),
    [
        (cts.point(10, 20), "point", "10,20"),
        (cts.point(-1.5, 0.25), "point", "-1.5,0.25"),
        (cts.box(1, 2, 3, 4), "box", "[1, 2, 3, 4]"),
        (cts.circle(5, cts.point(10, 20)), "circle", "@5 10,20"),
        (
            cts.polygon([cts.point(1, 2), cts.point(3, 4), cts.point(1, 2)]),
            "polygon",
            "1,2 3,4 1,2",
        ),
    ],
)
def test_region_type_and_text(region, region_type, text):
    assert region.region_type == region_type
    assert region.to_text() == text


@pytest.mark.parametrize(
    ("built", "cls"),
    [
        (cts.point(10, 20), Point),
        (cts.box(1, 2, 3, 4), Box),
        (cts.circle(5, cts.point(10, 20)), Circle),
        (cts.polygon("POLYGON((1 2, 3 4, 1 2))"), Polygon),
        (
            cts.period(datetime.datetime(2026, 1, 1), datetime.datetime(2027, 1, 1)),
            Period,
        ),
    ],
)
def test_builders_return_native_values(built, cls):
    assert isinstance(built, cls)


def test_constructed_region_equals_the_built_one():
    assert Point(10, 20) == cts.point(10, 20)
    assert Box(1, 2, 3, 4) == cts.box(1, 2, 3, 4)


@pytest.mark.parametrize(
    ("region", "message"),
    [
        (cts.point("POINT(20 10)"), "CTS point given as WKT text requires server"),
        (cts.polygon("POLYGON((1 2, 3 4, 1 2))"), "CTS polygon given as WKT text"),
        (cts.circle(5, xs.string("10,20")), "CTS point argument requires server"),
    ],
)
def test_region_text_requiring_evaluation_is_rejected(region, message):
    with pytest.raises(TypeError, match=message):
        region.to_text()
