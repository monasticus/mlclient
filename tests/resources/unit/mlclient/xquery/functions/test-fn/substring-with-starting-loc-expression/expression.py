from mlclient.xquery import cts, fn


def run():
    return fn.substring("source-string", fn.count(cts.search().pos(1))).compile()
