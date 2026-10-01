from mlclient.functions.xqy import fn


def run():
    return fn.replace("MarkLogic", "logic", "database", flags="i").compile()
