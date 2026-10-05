from mlclient.functions.xqy import cts, fn


def run():
    return fn.starts_with(fn.string(cts.search().pos(1)), "parameter2").compile()
