from mlclient.xquery import fn


def run():
    return fn.contains("parameter1", None).compile()
