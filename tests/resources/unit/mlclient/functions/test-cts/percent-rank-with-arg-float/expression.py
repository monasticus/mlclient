from mlclient.functions.xqy import cts


def run():
    return cts.percent_rank(2.5, "value").compile()
