from mlclient.functions.xqy import cts


def run():
    return cts.document_query("/products/1.xml").compile()
