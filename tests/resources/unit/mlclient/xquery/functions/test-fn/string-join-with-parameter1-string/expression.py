from mlclient.xquery import fn


def run():
    return fn.string_join("parameter1", "parameter2").compile()
