"""Test GeoRegionConstraintQuery through its public API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import GeoRegionConstraintQuery, Point


def run():
    query = GeoRegionConstraintQuery(
        "location",
        Point(10, 20),
        operator="intersects",
        weight=2,
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
