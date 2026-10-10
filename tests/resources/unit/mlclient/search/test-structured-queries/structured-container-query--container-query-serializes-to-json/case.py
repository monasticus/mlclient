"""Test ContainerQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import ContainerQuery, Element, TermQuery


def run():
    query = ContainerQuery(
        Element("section", "urn:example"),
        TermQuery("blue"),
        fragment_scope="properties",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
