from mlclient.xquery import fn


def run():
    return fn.index_of(2.5, "srch-param").compile()
