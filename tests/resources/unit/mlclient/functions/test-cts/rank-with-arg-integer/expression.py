from mlclient.functions.xqy import cts


def run():
    return cts.rank(123, "value").compile()
