from mlclient.xquery import cts


def run():
    return cts.element_words("item", query=cts.collection_query("products")).compile()
