from mlclient.xquery import cts


def run():
    return cts.collection_query("/products/1.xml").compile()
