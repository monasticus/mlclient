from xml.etree.ElementTree import tostring

from mlclient.xquery import cts
from tests.utils.resources import read_query_expectation


def run():
    query = cts.element_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
        options="coordinate-system=wgs84",
        weight=3,
    )
    assert query.to_json() == read_query_expectation(__file__, "expected.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected.xml",
    )
