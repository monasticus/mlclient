from mlclient.xquery import cts, fn


def run():
    return fn.string_join(fn.string(cts.search().pos(1)), "parameter2").compile()
