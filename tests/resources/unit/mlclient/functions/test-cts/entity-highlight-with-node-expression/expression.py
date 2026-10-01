from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.entity_highlight(
        cts.search().index(1), StaticExpression("function($node, $queries) { $node }"),
    ).compile()
