from mlclient.functions.xqy import cts


def run():
    return cts.quality(node=cts.search().index(1)).compile()
