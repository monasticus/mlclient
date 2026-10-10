"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-value-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementAttributeValueQuery, cts


def run():
    query = cts.element_attribute_value_query(
        "item",
        "status",
        "ok",
        options="exact",
        weight=0.5,
    )
    assert isinstance(query, ElementAttributeValueQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
