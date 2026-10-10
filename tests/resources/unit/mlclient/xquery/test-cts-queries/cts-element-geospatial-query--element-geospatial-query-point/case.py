"""Serialization through the public CTS builder.

Native constructor: ``cts:element-geospatial-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementGeospatialQuery, cts


def run():
    query = cts.element_geospatial_query(
        "origin",
        cts.point(10.5, -20.25),
        options="coordinate-system=wgs84",
        weight=2,
    )
    assert isinstance(query, ElementGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
