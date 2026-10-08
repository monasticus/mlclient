from mlclient.xquery import fn


def run():
    return fn.matches("MarkLogic", "logic", flags=None).compile()
