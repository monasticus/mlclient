from mlclient.functions.xqy import cts


def run():
    return cts.contains(cts.search().pos(1), set())
