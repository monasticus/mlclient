from mlclient.functions.xqy import cts


def run():
    return cts.triple_range_query(True, "predicate", "object").compile()
