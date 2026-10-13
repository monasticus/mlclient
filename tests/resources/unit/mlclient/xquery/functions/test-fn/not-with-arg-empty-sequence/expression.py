from mlclient.xquery import fn


def run():
    return fn.not_(None).compile()
