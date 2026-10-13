from mlclient.xquery import cts, fn


def run():
    return fn.string_length(fn.string(cts.search().pos(1))).compile()
