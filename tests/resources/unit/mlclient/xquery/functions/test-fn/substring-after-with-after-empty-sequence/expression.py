from mlclient.xquery import fn


def run():
    return fn.substring_after("MarkLogic", None).compile()
