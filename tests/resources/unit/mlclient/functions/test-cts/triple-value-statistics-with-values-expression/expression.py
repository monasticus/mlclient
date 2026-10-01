from mlclient.functions.xqy import cts, fn


def run():
    return cts.triple_value_statistics(values=fn.count(cts.search().index(1))).compile()
