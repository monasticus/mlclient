from mlclient.xquery import cts


def run():
    return cts.uri_match("prod*", query=cts.collection_query("products")).compile()
