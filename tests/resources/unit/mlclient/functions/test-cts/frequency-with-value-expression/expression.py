from mlclient.functions.xqy import cts


def run():
    return cts.frequency(cts.search().index(1)).compile()
