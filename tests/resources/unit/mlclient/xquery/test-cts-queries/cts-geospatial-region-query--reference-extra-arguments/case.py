"""Public compilation and native serialization of GeospatialRegionQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import cts


def run():
    query = cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region",
            options=["unchecked", "coordinate-system=wgs84"],
            geohash_precision=4,
            units="km",
            invalid_values="reject",
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
    )
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
