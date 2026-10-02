from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.similar_query(
        cts.search().pos(1), weight=2.5, options=StaticExpression("map:map()"),
    ).compile()
