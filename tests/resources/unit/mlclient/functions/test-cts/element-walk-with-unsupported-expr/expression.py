from mlclient.functions.xqy import cts


def run():
    return cts.element_walk(cts.search().index(1), "item", set())
