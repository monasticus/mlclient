from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.geospatial_region_path_reference(
        "/p:item",
        options="checked",
        namespaces=StaticExpression("map:map()"),
        geohash_precision=123,
        units="miles",
        invalid_values="reject",
    ).compile()
