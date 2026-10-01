from mlclient.functions.xqy import cts, fn


def run():
    return cts.words(options=fn.string(cts.search().index(1))).compile()
