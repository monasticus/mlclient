from mlclient.functions.xqy import cts


def run():
    return cts.triple_value_statistics(values="values", forest_ids=123).compile()
