from mlclient.xquery import cts


def run():
    return cts.walk(cts.search().pos(1), "needle", set())
