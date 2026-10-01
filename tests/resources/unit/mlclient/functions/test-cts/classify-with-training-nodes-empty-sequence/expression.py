from mlclient.functions.xqy import cts


def run():
    return cts.classify(
        cts.search().index(1),
        cts.train(cts.search().index(1), cts.search().index(2)),
        training_nodes=None,
    ).compile()
