from mlclient.xquery import cts


def run():
    return cts.train(None, cts.search().pos(1)).compile()
