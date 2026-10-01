from mlclient.functions.xqy import fn


def run():
    return fn.tokenize("MarkLogic", "logic", flags="i").compile()
