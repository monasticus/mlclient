from mlclient.functions.xqy import cts, fn


def run():
    return cts.triple_range_query(
        fn.count(cts.search().index(1)), "predicate", "object",
    ).compile()
