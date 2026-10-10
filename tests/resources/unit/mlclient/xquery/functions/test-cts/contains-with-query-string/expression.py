from mlclient.xquery import cts


def run():
    return cts.contains(cts.search().pos(1), "needle").compile()
