from mlclient.xquery import cts


def run():
    return cts.search(quality_weight=None).compile()
