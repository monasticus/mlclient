from mlclient.functions.xqy import cts


def run():
    return cts.estimate(maximum=2.5).compile()
