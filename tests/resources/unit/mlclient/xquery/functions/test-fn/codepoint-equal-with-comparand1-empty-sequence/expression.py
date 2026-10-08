from mlclient.xquery import fn


def run():
    return fn.codepoint_equal(None, "comparand2").compile()
