"""Test WordQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import Attribute, Element, WordQuery


def run():
    query = WordQuery(
        [Element("title"), Element("label")],
        ["blue", "green"],
        attribute=[Attribute("name"), Attribute("alt")],
        options=["case-sensitive"],
        weight=2,
        fragment_scope="documents",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
