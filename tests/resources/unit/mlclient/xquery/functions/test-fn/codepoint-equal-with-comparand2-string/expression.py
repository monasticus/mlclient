from mlclient.xquery import fn


def run():
    return fn.codepoint_equal("comparand1", "comparand2").compile()
