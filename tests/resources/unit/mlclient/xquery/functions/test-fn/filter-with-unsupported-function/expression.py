from mlclient.xquery import cts, fn


def run():
    return fn.filter(object(), cts.search().pos(1))
