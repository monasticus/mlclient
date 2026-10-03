from mlclient.functions.xqy import cts


def run():
    return cts.triple_range_query(123, "predicate", "object").compile()
