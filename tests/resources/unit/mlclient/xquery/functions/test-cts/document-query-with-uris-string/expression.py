from mlclient.xquery import cts


def run():
    return cts.document_query("/products/1.xml").compile()
