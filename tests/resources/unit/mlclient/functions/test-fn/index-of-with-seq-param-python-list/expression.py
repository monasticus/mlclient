from mlclient.functions.xqy import fn


def run():
    return fn.index_of(["seq-param", 2, 2.5, True], "srch-param").compile()
