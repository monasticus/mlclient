from mlclient.functions.xqy import cts


def run():
    return cts.fitness(node=cts.search().index(1)).compile()
