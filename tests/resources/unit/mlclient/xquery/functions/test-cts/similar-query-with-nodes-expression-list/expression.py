from mlclient.xquery import cts


def run():
    return cts.similar_query([cts.search().pos(1), cts.search().pos(2)]).compile()
