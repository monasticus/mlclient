from mlclient.xquery import cts


def run():
    return cts.percent_rank(123, "value").compile()
