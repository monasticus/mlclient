from mlclient.xquery import fn


def run():
    return fn.index_of("seq-param", "srch-param").compile()
