from mlclient.xquery import cts


def run():
    return cts.uris(options=["checked"]).compile()
