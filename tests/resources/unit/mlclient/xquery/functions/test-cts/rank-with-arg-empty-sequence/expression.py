from mlclient.xquery import cts


def run():
    return cts.rank(None, "value").compile()
