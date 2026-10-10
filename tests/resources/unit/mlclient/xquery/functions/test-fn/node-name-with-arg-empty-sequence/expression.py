from mlclient.xquery import fn


def run():
    return fn.node_name(None).compile()
