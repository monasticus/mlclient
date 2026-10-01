from mlclient.functions.xqy import cts


def run():
    return cts.classify(
        None, cts.train(cts.search().index(1), cts.search().index(2)),
    ).compile()
