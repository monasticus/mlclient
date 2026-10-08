from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.cluster(
        cts.search().pos(1), options=StaticExpression("map:map()"),
    ).compile()
