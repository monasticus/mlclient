from mlclient.xquery import fn


def run():
    return fn.avg(2.5).compile()
