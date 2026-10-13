from mlclient.xquery import fn


def run():
    return fn.default_collation().compile()
