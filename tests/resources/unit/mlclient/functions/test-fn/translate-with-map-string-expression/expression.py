from mlclient.functions.xqy import cts, fn


def run():
    return fn.translate("src", fn.string(cts.search().index(1)), "ABC").compile()
