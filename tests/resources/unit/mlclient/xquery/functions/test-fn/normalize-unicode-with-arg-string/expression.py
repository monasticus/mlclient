from mlclient.xquery import fn


def run():
    return fn.normalize_unicode("arg").compile()
