from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.entity_highlight(
        cts.search().pos(1), StaticExpression("function($node, $queries) { $node }"),
    ).compile()
