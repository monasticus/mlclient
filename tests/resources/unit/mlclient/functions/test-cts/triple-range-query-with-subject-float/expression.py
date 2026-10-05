from mlclient.functions.xqy import cts


def run():
    return cts.triple_range_query(2.5, "predicate", "object").compile()
