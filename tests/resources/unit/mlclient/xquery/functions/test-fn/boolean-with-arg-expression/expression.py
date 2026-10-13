from mlclient.xquery import cts, fn


def run():
    return fn.boolean(cts.search().pos(1)).compile()
