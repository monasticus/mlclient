"""Serialization through the public CTS builder.

Native constructor: ``cts:element-geospatial-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementGeospatialQuery, cts


def run():
    query = cts.element_geospatial_query(
        "origin",
        [
            cts.box(1.5, 2, 3, 4),
            cts.circle(5, cts.point(10, 20)),
            cts.polygon(
                [cts.point(0, 0), cts.point(0, 1), cts.point(1, 1), cts.point(0, 0)],
            ),
        ],
    )
    assert isinstance(query, ElementGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
