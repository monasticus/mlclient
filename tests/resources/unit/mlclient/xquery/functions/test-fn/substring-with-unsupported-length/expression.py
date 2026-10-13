from mlclient.xquery import fn


def run():
    return fn.substring("source-string", 2.5, length=object())
