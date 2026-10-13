from mlclient.xquery import fn


def run():
    return fn.index_of(2, "srch-param").compile()
