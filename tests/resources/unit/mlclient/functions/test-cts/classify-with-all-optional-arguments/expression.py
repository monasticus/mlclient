from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.classify(
        cts.search().pos(1),
        cts.train(cts.search().pos(1), cts.search().pos(2)),
        options=StaticExpression("map:map()"),
        training_nodes=cts.search().pos(1),
    ).compile()
