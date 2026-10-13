from mlclient.xquery import cts


def run():
    return cts.contains(None, "needle").compile()
