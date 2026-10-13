from mlclient.search.structured import ValueConstraintQuery


def run():
    return ValueConstraintQuery("status", ["blue", "green"], weight=2)
