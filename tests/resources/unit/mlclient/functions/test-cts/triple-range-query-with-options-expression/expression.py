from mlclient.functions.xqy import cts, fn


def run():
    return cts.triple_range_query(
        "subject", "predicate", "object", options=fn.string(cts.search().index(1)),
    ).compile()
