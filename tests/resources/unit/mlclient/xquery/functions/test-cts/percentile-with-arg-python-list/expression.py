from mlclient.xquery import cts


def run():
    return cts.percentile([2.5], 2.5).compile()
