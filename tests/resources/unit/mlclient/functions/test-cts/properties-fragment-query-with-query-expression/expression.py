from mlclient.functions.xqy import cts


def run():
    return cts.properties_fragment_query(cts.collection_query("products")).compile()
