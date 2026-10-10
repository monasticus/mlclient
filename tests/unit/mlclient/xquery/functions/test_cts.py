from __future__ import annotations

import pytest

from tests.utils.resources import discover_query_cases, discover_xqy_compilation_cases


@pytest.mark.parametrize(
    "case",
    discover_xqy_compilation_cases(__file__) + discover_query_cases(__file__),
    ids=lambda case: case.name,
)
def test_cts(case):
    case.assert_matches()
