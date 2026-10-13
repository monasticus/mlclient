from mlclient.xquery import cts


def run():
    return cts.reverse_query(cts.search().pos(1), weight=set())
