from mlclient.xquery import cts


def run():
    return cts.path_reference("/p:item", namespaces=None).compile()
