from mlclient.xquery import fn


def run():
    return fn.element_available("item").compile()
