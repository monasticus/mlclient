from mlclient.xquery import cts


def run():
    return cts.rank(["arg", 123, 2.5, True], "value").compile()
