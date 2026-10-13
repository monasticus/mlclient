from mlclient.xquery import fn


def run():
    return fn.index_of("seq-param", 2.5).compile()
