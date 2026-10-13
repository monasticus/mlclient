from mlclient.xquery import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.highlight(
        cts.search().pos(1),
        "needle",
        [
            StaticExpression("function($node, $queries) { $node }"),
            StaticExpression("function($node, $queries) { $node }"),
        ],
    ).compile()
