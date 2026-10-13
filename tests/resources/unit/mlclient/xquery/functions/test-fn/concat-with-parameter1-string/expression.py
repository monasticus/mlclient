from mlclient.xquery import fn


def run():
    return fn.concat("parameter1", "parameters").compile()
