from mlclient.functions.xqy import cts, fn


def run():
    return cts.lsqt_query("temporal", weight=fn.count(cts.search().index(1))).compile()
