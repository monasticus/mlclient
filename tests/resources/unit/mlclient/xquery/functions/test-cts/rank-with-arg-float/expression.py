from mlclient.xquery import cts


def run():
    return cts.rank(2.5, "value").compile()
