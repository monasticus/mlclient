from mlclient.xquery import cts


def run():
    return cts.triple_range_query(
        ["subject", 123, 2.5, True], "predicate", "object",
    ).compile()
