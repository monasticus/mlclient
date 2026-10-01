from mlclient.functions.xqy import cts, fn


def run():
    return fn.matches("MarkLogic", fn.string(cts.search().index(1))).compile()
