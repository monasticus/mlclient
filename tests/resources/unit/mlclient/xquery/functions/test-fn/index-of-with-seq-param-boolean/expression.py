from mlclient.xquery import fn


def run():
    return fn.index_of(True, "srch-param").compile()
