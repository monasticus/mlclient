"""Test GeoRegionPathQuery through its public API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point


def run():
    query = GeoRegionPathQuery(
        PathIndex("/place/region"),
        Point(10, 20),
        operator="intersects",
        coord="wgs84",
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
