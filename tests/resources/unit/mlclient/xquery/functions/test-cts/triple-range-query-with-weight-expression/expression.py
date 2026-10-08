from mlclient.xquery import cts, fn


def run():
    return cts.triple_range_query(
        "subject", "predicate", "object", weight=fn.count(cts.search().pos(1)),
    ).compile()
