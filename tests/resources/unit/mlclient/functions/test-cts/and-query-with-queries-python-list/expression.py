from mlclient.functions.xqy import cts


def run():
    return cts.and_query(["queries"]).compile()
