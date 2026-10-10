"""Native serialization resources and public query behavior."""

import pytest
from tests.utils.resources import discover_serialization_cases
from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point
from mlclient.search.structured import PeriodCompareQuery
from decimal import Decimal
from mlclient.search.structured import Element, RangeQuery
from mlclient.search.structured import TermQuery


@pytest.mark.parametrize(
    "case", discover_serialization_cases(__file__), ids=lambda case: case.name,
)
def test_serialization(case):
    case.assert_matches()


def test_structured_geo_region_path_query_accepts_native_operator():
    GeoRegionPathQuery(PathIndex("/region"), Point(10, 20), operator="covered-by")


def test_structured_period_compare_query_accepts_native_operator():
    PeriodCompareQuery("system", "iso_equals", "valid")


def test_structured_term_query_range_query_values_may_be_non_finite():
    query = RangeQuery(Element("price"), Decimal("NaN"), operator="LT")
    assert query.to_json()["range-query"]["value"] == "NaN"


@pytest.mark.parametrize("weight", [Decimal("NaN"), Decimal("Infinity"), float("-inf")])
def test_structured_term_query_term_query_rejects_a_non_finite_weight(weight):
    with pytest.raises(ValueError, match="must be finite") as exc:
        TermQuery("blue", weight=weight)
    assert str(exc.value) == "TermQuery.weight must be finite."
