from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_range_query("valid", fn.string(cts.search().pos(1))).compile()
