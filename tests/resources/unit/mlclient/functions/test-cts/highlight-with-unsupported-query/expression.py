from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.highlight(
        cts.search().index(1),
        set(),
        StaticExpression("function($node, $queries) { $node }"),
    )
