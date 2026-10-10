from mlclient.xquery import cts


def run():
    return cts.words(quality_weight=2.5).compile()
