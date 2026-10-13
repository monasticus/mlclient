from mlclient.xquery import fn


def run():
    return fn.generate_id(None).compile()
