from mlclient.functions.xqy import cts


def run():
    return cts.near_query(
        "queries", distance=2.5, options="checked", distance_weight=2.5,
    ).compile()
