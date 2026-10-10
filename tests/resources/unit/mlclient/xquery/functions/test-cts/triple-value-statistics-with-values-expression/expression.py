from mlclient.xquery import cts, fn


def run():
    return cts.triple_value_statistics(values=fn.count(cts.search().pos(1))).compile()
