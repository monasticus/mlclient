from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_values("item", start=fn.count(cts.search().index(1))).compile()
