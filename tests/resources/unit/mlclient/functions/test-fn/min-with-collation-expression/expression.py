from mlclient.functions.xqy import cts, fn


def run():
    return fn.min("arg", collation=fn.string(cts.search().index(1))).compile()
