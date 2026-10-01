from mlclient.functions.xqy import cts
from tests.utils.expressions import StaticExpression


def run():
    return cts.classify(
        cts.search().index(1),
        cts.train(cts.search().index(1), cts.search().index(2)),
        options=StaticExpression("map:map()"),
        training_nodes=cts.search().index(1),
    ).compile()
