from mlclient.xquery import cts


def run():
    return cts.element_query("item", cts.collection_query("products")).compile()
