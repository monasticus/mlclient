from mlclient.xquery import cts


def run():
    return cts.cluster(cts.search().pos(1), options=set())
