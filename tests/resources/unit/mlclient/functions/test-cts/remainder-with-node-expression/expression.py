from mlclient.functions.xqy import cts


def run():
    return cts.remainder(node=cts.search().index(1)).compile()
