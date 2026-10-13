from mlclient.xquery import fn


def run():
    return fn.starts_with("parameter1", "parameter2", collation=None).compile()
