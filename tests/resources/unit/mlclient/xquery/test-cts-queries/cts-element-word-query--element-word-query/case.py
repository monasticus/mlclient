"""Native ``cts:element-word-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementWordQuery, cts, fn

NS = "urn:mlclient:cts-test"


def run():
    query = cts.element_word_query(
        fn.qname(NS, "title"),
        ["blue", "red"],
        options="case-insensitive",
        weight=2,
    )
    assert isinstance(query, ElementWordQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
