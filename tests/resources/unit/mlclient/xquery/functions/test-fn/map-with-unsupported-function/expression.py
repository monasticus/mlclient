from mlclient.xquery import cts, fn


def run():
    return fn.map(object(), cts.search().pos(1))
