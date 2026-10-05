from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.entity_walk(
        set(), StaticExpression("function($node, $queries) { $node }"),
    )
