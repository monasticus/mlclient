from mlclient.xquery import cts


def run():
    return cts.uri_match("prod*", options=["checked"]).compile()
