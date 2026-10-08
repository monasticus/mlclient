from mlclient.xquery import fn


def run():
    return fn.min("arg", collation=None).compile()
