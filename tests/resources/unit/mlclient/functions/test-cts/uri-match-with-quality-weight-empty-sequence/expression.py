from mlclient.functions.xqy import cts


def run():
    return cts.uri_match("prod*", quality_weight=None).compile()
