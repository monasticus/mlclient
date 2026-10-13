from mlclient.xquery import fn


def run():
    return fn.current_grouping_key().compile()
