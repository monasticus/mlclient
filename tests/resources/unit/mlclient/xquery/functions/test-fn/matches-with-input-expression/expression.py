from mlclient.xquery import cts, fn


def run():
    return fn.matches(fn.string(cts.search().pos(1)), "logic").compile()
