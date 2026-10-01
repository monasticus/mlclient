from mlclient.functions.xqy import cts


def run():
    return cts.walk(cts.search().index(1), "needle", set())
