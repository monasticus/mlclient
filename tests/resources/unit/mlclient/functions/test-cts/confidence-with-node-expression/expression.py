from mlclient.functions.xqy import cts


def run():
    return cts.confidence(node=cts.search().pos(1)).compile()
