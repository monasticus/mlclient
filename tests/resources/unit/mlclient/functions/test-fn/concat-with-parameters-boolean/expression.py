from mlclient.functions.xqy import fn


def run():
    return fn.concat("parameter1", True).compile()
