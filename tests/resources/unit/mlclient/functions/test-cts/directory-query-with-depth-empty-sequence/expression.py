from mlclient.functions.xqy import cts


def run():
    return cts.directory_query("/products/1.xml", None).compile()
