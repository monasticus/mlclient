from mlclient.functions.xqy import fn


def run():
    return fn.substring_after("MarkLogic", "needle").compile()
