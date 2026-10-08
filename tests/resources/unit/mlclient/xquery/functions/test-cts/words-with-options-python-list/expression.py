from mlclient.xquery import cts


def run():
    return cts.words(options=["checked"]).compile()
