from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.entity_highlight(
        set(), StaticExpression("function($node, $queries) { $node }"),
    )
