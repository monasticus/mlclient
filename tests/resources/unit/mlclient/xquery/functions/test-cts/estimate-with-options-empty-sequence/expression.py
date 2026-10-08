from mlclient.xquery import cts


def run():
    return cts.estimate(options=None).compile()
