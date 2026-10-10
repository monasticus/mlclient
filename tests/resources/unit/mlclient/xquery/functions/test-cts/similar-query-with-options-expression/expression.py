from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.similar_query(
        cts.search().pos(1), options=StaticExpression("map:map()"),
    ).compile()
