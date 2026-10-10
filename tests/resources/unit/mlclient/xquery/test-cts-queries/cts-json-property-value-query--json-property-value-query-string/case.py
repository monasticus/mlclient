"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-value-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import JsonPropertyValueQuery, cts


def run():
    query = cts.json_property_value_query("label", "gamma")
    assert isinstance(query, JsonPropertyValueQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
