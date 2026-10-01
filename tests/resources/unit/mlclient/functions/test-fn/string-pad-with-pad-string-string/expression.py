from mlclient.functions.xqy import fn


def run():
    return fn.string_pad("pad-string", 2).compile()
