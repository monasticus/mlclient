from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.geospatial_region_path_reference(
        "/p:item", namespaces=StaticExpression("map:map()"),
    ).compile()
