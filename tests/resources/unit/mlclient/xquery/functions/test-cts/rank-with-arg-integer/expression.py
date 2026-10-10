from mlclient.xquery import cts


def run():
    return cts.rank(123, "value").compile()
