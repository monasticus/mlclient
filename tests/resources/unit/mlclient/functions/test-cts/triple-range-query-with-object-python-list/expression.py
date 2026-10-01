from mlclient.functions.xqy import cts


def run():
    return cts.triple_range_query(
        "subject", "predicate", ["object", 123, 2.5, True],
    ).compile()
