from mlclient.functions.xqy import cts


def run():
    return cts.near_query("queries", options=None).compile()
