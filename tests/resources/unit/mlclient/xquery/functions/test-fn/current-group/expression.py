from mlclient.xquery import fn


def run():
    return fn.current_group().compile()
