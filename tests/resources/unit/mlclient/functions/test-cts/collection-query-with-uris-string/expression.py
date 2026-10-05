from mlclient.functions.xqy import cts


def run():
    return cts.collection_query("/products/1.xml").compile()
