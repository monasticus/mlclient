from mlclient.xquery import fn


def run():
    return fn.avg(True).compile()
