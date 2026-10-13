from mlclient.xquery import cts


def run():
    return cts.frequency(cts.search().pos(1)).compile()
