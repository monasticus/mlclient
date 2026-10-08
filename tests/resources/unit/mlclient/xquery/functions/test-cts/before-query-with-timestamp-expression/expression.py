from mlclient.xquery import cts, fn


def run():
    return cts.before_query(fn.count(cts.search().pos(1))).compile()
