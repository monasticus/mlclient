from mlclient.xquery import fn


def run():
    return fn.concat("parameter1", True).compile()
