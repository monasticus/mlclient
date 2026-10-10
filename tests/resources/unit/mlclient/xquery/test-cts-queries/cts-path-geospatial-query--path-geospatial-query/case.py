"""Native ``cts:path-geospatial-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import PathGeospatialQuery, cts


def run():
    query = cts.path_geospatial_query("/item/origin", cts.point(10, 20))
    assert isinstance(query, PathGeospatialQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
