from mlclient.xquery import cts


def run():
    return cts.classify(
        cts.search().pos(1),
        cts.train(cts.search().pos(1), cts.search().pos(2)),
        training_nodes=cts.search().pos(1),
    ).compile()
