from mlclient.functions.xqy import cts


def run():
    return cts.similar_query(cts.search().pos(1), weight=2.5).compile()
