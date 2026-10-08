from mlclient.xquery import cts, fn


def run():
    return fn.string_pad("pad-string", fn.count(cts.search().pos(1))).compile()
