from mlclient.functions.xqy import cts, fn


def run():
    return cts.lsqt_query(fn.string(cts.search().index(1))).compile()
