"""Test NearQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import NearQuery, TermQuery


def run():
    query = NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
