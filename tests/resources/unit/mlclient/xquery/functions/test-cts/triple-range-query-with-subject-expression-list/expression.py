from mlclient.xquery import cts, fn


def run():
    return cts.triple_range_query(
        [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
        "predicate",
        "object",
    ).compile()
