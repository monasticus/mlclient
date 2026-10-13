from mlclient.xquery import cts, fn


def run():
    return fn.replace(fn.string(cts.search().pos(1)), "logic", "database").compile()
