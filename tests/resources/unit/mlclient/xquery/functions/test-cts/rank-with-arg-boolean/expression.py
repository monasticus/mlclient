from mlclient.xquery import cts


def run():
    return cts.rank(True, "value").compile()
