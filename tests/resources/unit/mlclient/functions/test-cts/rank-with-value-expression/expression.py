from mlclient.functions.xqy import cts, fn


def run():
    return cts.rank("arg", fn.count(cts.search().index(1))).compile()
