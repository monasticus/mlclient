"""Test ValueQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    query = ValueQuery(
        JsonProperty("active"),
        True,
        node_type="boolean",
        options=["exact"],
        weight=2,
        fragment_scope="documents",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
