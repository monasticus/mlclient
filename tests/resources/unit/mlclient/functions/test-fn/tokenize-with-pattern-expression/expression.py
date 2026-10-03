from mlclient.functions.xqy import cts, fn


def run():
    return fn.tokenize("MarkLogic", fn.string(cts.search().pos(1))).compile()
