"""Concrete search components serialize to the expected JSON and XML."""

import pytest

from tests.utils.resources import discover_serialization_cases


@pytest.mark.parametrize(
    "case",
    discover_serialization_cases(__file__),
    ids=lambda case: case.name,
)
def test_serialization(case):
    case.assert_matches()
