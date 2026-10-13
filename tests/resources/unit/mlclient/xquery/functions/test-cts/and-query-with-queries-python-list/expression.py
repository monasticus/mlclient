from mlclient.xquery import cts


def run():
    return cts.and_query(["queries"]).compile()
