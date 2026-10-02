from mlclient.functions.xqy import cts


def run():
    return cts.search(cts.search().pos(1)).compile()
