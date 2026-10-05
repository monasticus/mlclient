from mlclient.functions.xqy import cts


def run():
    return cts.uri_match("prod*", quality_weight=2.5).compile()
