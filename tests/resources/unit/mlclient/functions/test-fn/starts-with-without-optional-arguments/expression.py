from mlclient.functions.xqy import fn


def run():
    return fn.starts_with("parameter1", "parameter2").compile()
