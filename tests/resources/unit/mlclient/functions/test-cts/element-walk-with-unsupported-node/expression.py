from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.element_walk(
        set(), "item", StaticExpression("function($node, $queries) { $node }"),
    )
