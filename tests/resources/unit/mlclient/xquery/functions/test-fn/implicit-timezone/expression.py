from mlclient.xquery import fn


def run():
    return fn.implicit_timezone().compile()
