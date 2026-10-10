"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-pair-geospatial-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementAttributePairGeospatialQuery, cts


def run():
    query = cts.element_attribute_pair_geospatial_query(
        "item",
        "lat",
        "lon",
        cts.point(10, 20),
        weight=3,
    )
    assert isinstance(query, ElementAttributePairGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
