from mlclient.xquery import cts, fn


def run():
    return fn.matches("MarkLogic", fn.string(cts.search().pos(1))).compile()
