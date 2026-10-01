from mlclient.functions.xqy import cts, fn


def run():
    return cts.near_query(
        "queries", distance_weight=fn.count(cts.search().index(1)),
    ).compile()
