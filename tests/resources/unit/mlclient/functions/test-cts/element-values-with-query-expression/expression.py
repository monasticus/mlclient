from mlclient.functions.xqy import cts


def run():
    return cts.element_values("item", query=cts.collection_query("products")).compile()
