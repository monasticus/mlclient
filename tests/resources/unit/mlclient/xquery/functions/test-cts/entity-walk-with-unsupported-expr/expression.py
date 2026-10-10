from mlclient.xquery import cts


def run():
    return cts.entity_walk(cts.search().pos(1), set())
