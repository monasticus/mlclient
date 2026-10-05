from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.geospatial_path_reference(
        "/p:item", map=StaticExpression("map:map()"),
    ).compile()
