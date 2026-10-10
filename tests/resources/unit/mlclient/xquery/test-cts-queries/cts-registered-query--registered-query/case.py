"""Native ``cts:registered-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import RegisteredQuery, cts


def run():
    query = cts.registered_query([1, 2], options="unfiltered", weight=2)
    assert isinstance(query, RegisteredQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
