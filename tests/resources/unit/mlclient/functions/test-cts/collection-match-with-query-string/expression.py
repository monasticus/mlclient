from mlclient.functions.xqy import cts


def run():
    return cts.collection_match("prod*", query="needle").compile()
