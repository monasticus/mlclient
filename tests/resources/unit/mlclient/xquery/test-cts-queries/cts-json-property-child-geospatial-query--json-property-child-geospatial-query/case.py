"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-child-geospatial-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import JsonPropertyChildGeospatialQuery, cts


def run():
    query = cts.json_property_child_geospatial_query(
        "location",
        "point",
        cts.point(10, 20),
    )
    assert isinstance(query, JsonPropertyChildGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
