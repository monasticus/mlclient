from mlclient.functions.xqy import cts


def run():
    return cts.contains(cts.search().index(1), set())
