from mlclient.xquery import cts


def run():
    return cts.train(cts.search().pos(1), cts.search().pos(1), options=set())
