from mlclient.xquery import cts


def run():
    return cts.words(quality_weight=None).compile()
