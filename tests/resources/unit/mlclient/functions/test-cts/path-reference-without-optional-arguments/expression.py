from mlclient.functions.xqy import cts


def run():
    return cts.path_reference("/p:item").compile()
