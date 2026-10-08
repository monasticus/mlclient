from mlclient.xquery import cts


def run():
    return cts.triple_range_query(123, "predicate", "object").compile()
