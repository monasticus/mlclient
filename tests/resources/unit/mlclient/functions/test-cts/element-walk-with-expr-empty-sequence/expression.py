from mlclient.functions.xqy import cts


def run():
    return cts.element_walk(cts.search().pos(1), "item", None).compile()
