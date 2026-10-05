from mlclient.functions.xqy import cts


def run():
    return cts.remainder(node=cts.search().pos(1)).compile()
