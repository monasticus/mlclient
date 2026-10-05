from mlclient.functions.xqy import cts


def run():
    return cts.contains(None, "needle").compile()
