from mlclient.xquery import cts


def run():
    return cts.triple_value_statistics(forest_ids=123).compile()
