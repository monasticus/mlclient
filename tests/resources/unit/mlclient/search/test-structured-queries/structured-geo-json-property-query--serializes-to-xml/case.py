"""Test GeoJsonPropertyQuery through its public API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import GeoJsonPropertyQuery, JsonProperty, Point


def run():
    query = GeoJsonPropertyQuery(
        JsonProperty("location"),
        Point(10, 20),
        parent=JsonProperty("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
