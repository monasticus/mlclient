from mlclient.functions.xqy import cts


def run():
    return cts.confidence(node=cts.search().index(1)).compile()
