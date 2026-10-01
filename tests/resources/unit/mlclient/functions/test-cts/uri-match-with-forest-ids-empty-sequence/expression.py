from mlclient.functions.xqy import cts


def run():
    return cts.uri_match("prod*", forest_ids=None).compile()
