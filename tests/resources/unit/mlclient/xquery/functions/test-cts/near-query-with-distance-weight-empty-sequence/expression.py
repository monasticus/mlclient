from mlclient.xquery import cts


def run():
    return cts.near_query("queries", distance_weight=None).compile()
