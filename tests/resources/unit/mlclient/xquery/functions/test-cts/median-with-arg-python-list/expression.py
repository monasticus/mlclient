from mlclient.xquery import cts


def run():
    return cts.median([2.5]).compile()
