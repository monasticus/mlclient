from mlclient.xquery import cts


def run():
    return cts.fitness_order(options=["checked"]).compile()
