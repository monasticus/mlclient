"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-pair-geospatial-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import JsonPropertyPairGeospatialQuery, cts


def run():
    query = cts.json_property_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
    )
    assert isinstance(query, JsonPropertyPairGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
