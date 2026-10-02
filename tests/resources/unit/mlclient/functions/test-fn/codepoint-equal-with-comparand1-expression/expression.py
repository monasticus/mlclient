from mlclient.functions.xqy import cts, fn


def run():
    return fn.codepoint_equal(fn.string(cts.search().pos(1)), "comparand2").compile()
