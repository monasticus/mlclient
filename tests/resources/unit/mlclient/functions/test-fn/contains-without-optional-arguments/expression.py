from mlclient.functions.xqy import fn


def run():
    return fn.contains("parameter1", "parameter2").compile()
