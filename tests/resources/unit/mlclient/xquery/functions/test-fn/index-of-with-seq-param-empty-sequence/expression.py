from mlclient.xquery import fn


def run():
    return fn.index_of(None, "srch-param").compile()
