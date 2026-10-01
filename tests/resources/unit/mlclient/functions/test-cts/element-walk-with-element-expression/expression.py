from mlclient.functions.xqy import cts, fn
from tests.utils.expressions import StaticExpression


def run():
    return cts.element_walk(
        cts.search().index(1),
        fn.qname("https://example.com/products", "p:item"),
        StaticExpression("function($node, $queries) { $node }"),
    ).compile()
