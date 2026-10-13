from mlclient.xquery import cts


def run():
    return cts.percent_rank(None, "value").compile()
