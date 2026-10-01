from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.train(
        cts.search().index(1),
        cts.search().index(1),
        options=StaticExpression("map:map()"),
    ).compile()
