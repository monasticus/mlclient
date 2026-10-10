from mlclient.xquery import cts


def run():
    return cts.words(start=None).compile()
