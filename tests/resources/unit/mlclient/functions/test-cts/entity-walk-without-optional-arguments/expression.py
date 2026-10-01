from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.entity_walk(
        cts.search().index(1), StaticExpression("function($node, $queries) { $node }"),
    ).compile()
