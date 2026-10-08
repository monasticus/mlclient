from mlclient.xquery import fn


def run():
    return fn.static_base_uri().compile()
