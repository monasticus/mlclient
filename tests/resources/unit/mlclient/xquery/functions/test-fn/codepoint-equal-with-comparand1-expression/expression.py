from mlclient.xquery import cts, fn


def run():
    return fn.codepoint_equal(fn.string(cts.search().pos(1)), "comparand2").compile()
