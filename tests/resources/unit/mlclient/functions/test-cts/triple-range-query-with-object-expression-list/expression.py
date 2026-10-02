from mlclient.functions.xqy import cts, fn


def run():
    return cts.triple_range_query(
        "subject",
        "predicate",
        [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
