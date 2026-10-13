from mlclient.xquery import fn


def run():
    return fn.string_pad(None, 2).compile()
