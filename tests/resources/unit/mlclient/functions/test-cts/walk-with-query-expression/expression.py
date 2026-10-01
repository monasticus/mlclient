from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.walk(
        cts.search().index(1),
        cts.collection_query("products"),
        StaticExpression("function($node, $queries) { $node }"),
    ).compile()
