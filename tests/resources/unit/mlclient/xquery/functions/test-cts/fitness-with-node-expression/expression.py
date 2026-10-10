from mlclient.xquery import cts


def run():
    return cts.fitness(node=cts.search().pos(1)).compile()
