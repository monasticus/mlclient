from mlclient.xquery import cts


def run():
    return cts.triple_range_query(None, "predicate", "object").compile()
