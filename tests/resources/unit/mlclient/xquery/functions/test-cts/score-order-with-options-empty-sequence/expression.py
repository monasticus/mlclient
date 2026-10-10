from mlclient.xquery import cts


def run():
    return cts.score_order(options=None).compile()
