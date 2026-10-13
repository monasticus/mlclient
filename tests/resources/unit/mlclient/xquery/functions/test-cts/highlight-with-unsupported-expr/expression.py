from mlclient.xquery import cts


def run():
    return cts.highlight(cts.search().pos(1), "needle", set())
