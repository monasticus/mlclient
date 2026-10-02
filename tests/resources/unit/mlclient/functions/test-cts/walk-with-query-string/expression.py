from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.walk(
        cts.search().pos(1),
        "needle",
        StaticExpression("function($node, $queries) { $node }"),
    ).compile()
