from mlclient.xquery import cts


def run():
    return cts.estimate(quality_weight=2.5).compile()
