from mlclient.xquery import cts


def run():
    return cts.near_query("queries", distance=2.5).compile()
