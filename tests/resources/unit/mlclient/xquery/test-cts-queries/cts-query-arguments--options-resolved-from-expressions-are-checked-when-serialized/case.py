"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts, xs


@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            cts.and_query([], options=xs.string("bogus")),
            (
                "cts:and-query: options ['bogus'] are not and-query opti"
                "ons; use at most one of ordered, unordered"
            ),
        ),
        (
            cts.or_query([], options=xs.string("ordered")),
            (
                "cts:or-query: options ['ordered'] are not or-query opti"
                "ons; use at most one of synonym"
            ),
        ),
    ],
)
def run(query, message):
    with pytest.raises(ValueError, match="are not") as error:
        query.to_json()
    assert str(error.value) == message
