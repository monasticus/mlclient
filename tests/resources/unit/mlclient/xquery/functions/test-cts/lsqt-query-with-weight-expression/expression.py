from mlclient.xquery import cts, fn


def run():
    return cts.lsqt_query("temporal", weight=fn.count(cts.search().pos(1))).compile()
