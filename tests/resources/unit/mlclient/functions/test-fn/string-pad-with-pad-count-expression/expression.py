from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_pad("pad-string", fn.count(cts.search().index(1))).compile()
