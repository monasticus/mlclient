from mlclient.functions.xqy import cts


def run():
    return cts.percent_rank(["arg", 123, 2.5, True], "value").compile()
