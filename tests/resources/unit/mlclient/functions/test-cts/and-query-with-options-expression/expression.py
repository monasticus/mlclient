from mlclient.functions.xqy import cts, fn


def run():
    return cts.and_query("queries", options=fn.string(cts.search().index(1))).compile()
