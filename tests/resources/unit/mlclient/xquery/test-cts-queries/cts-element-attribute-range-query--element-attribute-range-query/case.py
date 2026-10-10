"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-range-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementAttributeRangeQuery, cts


def run():
    query = cts.element_attribute_range_query("item", "amount", "!=", 3)
    assert isinstance(query, ElementAttributeRangeQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
