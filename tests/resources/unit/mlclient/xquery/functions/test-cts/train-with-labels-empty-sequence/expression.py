from mlclient.xquery import cts


def run():
    return cts.train(cts.search().pos(1), None).compile()
