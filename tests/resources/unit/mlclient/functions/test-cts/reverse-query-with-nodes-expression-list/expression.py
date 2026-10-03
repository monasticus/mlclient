from mlclient.functions.xqy import cts


def run():
    return cts.reverse_query([cts.search().pos(1), cts.search().pos(2)]).compile()
