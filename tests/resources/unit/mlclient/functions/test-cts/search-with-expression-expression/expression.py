from mlclient.functions.xqy import cts


def run():
    return cts.search(cts.search().index(1)).compile()
