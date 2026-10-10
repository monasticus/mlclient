"""Serialization through the public CTS builder.

Native constructor: ``cts:element-pair-geospatial-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementPairGeospatialQuery, cts


def run():
    query = cts.element_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
    )
    assert isinstance(query, ElementPairGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
