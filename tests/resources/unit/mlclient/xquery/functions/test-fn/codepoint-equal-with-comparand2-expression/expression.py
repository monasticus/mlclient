from mlclient.xquery import cts, fn


def run():
    return fn.codepoint_equal("comparand1", fn.string(cts.search().pos(1))).compile()
