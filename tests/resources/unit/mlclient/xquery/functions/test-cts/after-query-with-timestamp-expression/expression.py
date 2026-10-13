from mlclient.xquery import cts, fn


def run():
    return cts.after_query(fn.count(cts.search().pos(1))).compile()
