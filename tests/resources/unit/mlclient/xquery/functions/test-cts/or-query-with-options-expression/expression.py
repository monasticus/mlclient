from mlclient.xquery import cts, fn


def run():
    return cts.or_query("queries", options=fn.string(cts.search().pos(1))).compile()
