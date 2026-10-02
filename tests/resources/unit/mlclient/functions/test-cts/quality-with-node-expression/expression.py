from mlclient.functions.xqy import cts


def run():
    return cts.quality(node=cts.search().pos(1)).compile()
