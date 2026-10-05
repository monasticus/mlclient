from mlclient.functions.xqy import cts


def run():
    return cts.frequency(cts.search().pos(1)).compile()
