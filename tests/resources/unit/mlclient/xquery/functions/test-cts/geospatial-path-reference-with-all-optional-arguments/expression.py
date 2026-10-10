from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.geospatial_path_reference(
        "/p:item", options="checked", map=StaticExpression("map:map()"),
    ).compile()
