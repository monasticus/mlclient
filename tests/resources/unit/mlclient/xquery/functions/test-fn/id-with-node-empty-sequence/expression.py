from mlclient.xquery import fn


def run():
    return fn.id("arg", node=None).compile()
