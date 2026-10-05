from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.element_walk(
        cts.search().pos(1),
        ["item"],
        StaticExpression("function($node, $queries) { $node }"),
    ).compile()
