from mlclient.functions.xqy import cts


def run():
    return cts.cluster(cts.search().pos(1), options=None).compile()
