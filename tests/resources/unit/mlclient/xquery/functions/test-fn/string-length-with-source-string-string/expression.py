from mlclient.xquery import fn


def run():
    return fn.string_length("source-string").compile()
