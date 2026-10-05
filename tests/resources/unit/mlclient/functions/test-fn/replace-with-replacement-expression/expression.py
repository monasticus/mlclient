from mlclient.functions.xqy import cts, fn


def run():
    return fn.replace("MarkLogic", "logic", fn.string(cts.search().pos(1))).compile()
