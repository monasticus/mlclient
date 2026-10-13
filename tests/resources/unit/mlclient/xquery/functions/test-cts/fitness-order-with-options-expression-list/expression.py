from mlclient.xquery import cts, fn


def run():
    return cts.fitness_order(
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
