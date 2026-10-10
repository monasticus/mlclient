from mlclient.xquery import cts, fn


def run():
    return fn.substring_after("MarkLogic", fn.string(cts.search().pos(1))).compile()
