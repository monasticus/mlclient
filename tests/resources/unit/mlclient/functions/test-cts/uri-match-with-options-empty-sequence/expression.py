from mlclient.functions.xqy import cts


def run():
    return cts.uri_match("prod*", options=None).compile()
