from mlclient.xquery import fn


def run():
    return fn.replace("MarkLogic", "logic", "database", flags=None).compile()
