from mlclient.xquery import cts


def run():
    return cts.triple_value_statistics(values=["values", 123, 2.5, True]).compile()
