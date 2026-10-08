from mlclient.xquery import fn


def run():
    return fn.max("arg", collation=None).compile()
