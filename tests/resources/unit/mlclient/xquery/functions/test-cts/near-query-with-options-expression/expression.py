from mlclient.xquery import cts, fn


def run():
    return cts.near_query("queries", options=fn.string(cts.search().pos(1))).compile()
