from mlclient.functions.xqy import cts


def run():
    return cts.fitness(node=cts.search().pos(1)).compile()
