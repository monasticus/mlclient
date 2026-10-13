from mlclient.xquery import fn


def run():
    return fn.replace("MarkLogic", object(), "database")
