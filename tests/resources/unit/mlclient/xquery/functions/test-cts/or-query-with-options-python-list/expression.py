from mlclient.xquery import cts


def run():
    return cts.or_query("queries", options=["synonym"]).compile()
