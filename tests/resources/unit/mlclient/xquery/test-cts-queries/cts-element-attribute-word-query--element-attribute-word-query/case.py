"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-word-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementAttributeWordQuery, cts


def run():
    query = cts.element_attribute_word_query("item", "status", "ok")
    assert isinstance(query, ElementAttributeWordQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
