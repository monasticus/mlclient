from mlclient.functions.xqy import cts


def run():
    return cts.cluster(cts.search().index(1), options=None).compile()
