from mlclient.xquery import cts, fn


def run():
    return fn.substring_before("MarkLogic", fn.string(cts.search().pos(1))).compile()
