from mlclient.xquery import cts, fn


def run():
    return fn.key("product", fn.string(cts.search().pos(1))).compile()
