from mlclient.xquery import cts


def run():
    return cts.triple_value_statistics(values=True).compile()
