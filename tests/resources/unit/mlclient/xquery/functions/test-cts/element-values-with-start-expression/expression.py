from mlclient.xquery import cts, fn


def run():
    return cts.element_values("item", start=fn.count(cts.search().pos(1))).compile()
