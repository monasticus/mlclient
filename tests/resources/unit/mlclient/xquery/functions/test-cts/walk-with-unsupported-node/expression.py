from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.walk(
        set(), "needle", StaticExpression("function($node, $queries) { $node }"),
    )
