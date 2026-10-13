from mlclient.xquery import cts


def run():
    return cts.similar_query(cts.search().pos(1), options=set())
