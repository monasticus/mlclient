from mlclient.xquery import cts, fn


def run():
    return fn.insert_before(cts.search().pos(1), 2, object())
