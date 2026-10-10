"""Native ``cts:element-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementQuery, cts, fn

NS = "urn:mlclient:cts-test"


def run():
    query = cts.element_query(["a", fn.qname(NS, "t:b")], cts.word_query("x"))
    assert isinstance(query, ElementQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
