from mlclient.functions.xqy import cts, fn


def run():
    return cts.triple_range_query(
        fn.count(cts.search().pos(1)), "predicate", "object",
    ).compile()
