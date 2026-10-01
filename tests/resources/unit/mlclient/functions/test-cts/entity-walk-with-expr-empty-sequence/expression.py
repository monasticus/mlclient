from mlclient.functions.xqy import cts


def run():
    return cts.entity_walk(cts.search().index(1), None).compile()
