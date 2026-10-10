from mlclient.xquery import cts


def run():
    return cts.collection_match("prod*", quality_weight=None).compile()
