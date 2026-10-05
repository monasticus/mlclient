from mlclient.functions.xqy import cts, fn


def run():
    return cts.after_query(fn.count(cts.search().pos(1))).compile()
