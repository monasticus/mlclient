from mlclient.xquery import cts


def run():
    return cts.collection_match("prod*", forest_ids=123).compile()
