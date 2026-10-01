from mlclient.functions.xqy import cts


def run():
    return cts.collection_match("prod*", forest_ids=123).compile()
