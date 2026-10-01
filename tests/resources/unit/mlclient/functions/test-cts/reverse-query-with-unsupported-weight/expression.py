from mlclient.functions.xqy import cts


def run():
    return cts.reverse_query(cts.search().index(1), weight=set())
