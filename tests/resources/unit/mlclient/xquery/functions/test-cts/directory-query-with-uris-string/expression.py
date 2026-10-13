from mlclient.xquery import cts


def run():
    return cts.directory_query("/products/1.xml").compile()
