from mlclient.functions.xqy import cts, fn


def run():
    return fn.translate("src", "abc", fn.string(cts.search().index(1))).compile()
