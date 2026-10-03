from mlclient.functions.xqy import cts, fn


def run():
    return fn.analyze_string("MarkLogic", fn.string(cts.search().pos(1))).compile()
