"""Individually authored query contracts loaded from resources."""

import pytest

from tests.utils.resources import discover_query_cases


@pytest.mark.parametrize(
    "case",
    discover_query_cases(__file__),
    ids=lambda case: case.name,
)
def test_query_cases(case, request):
    case.assert_matches(request)
