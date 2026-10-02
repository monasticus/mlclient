from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_range_query(
        fn.string(cts.search().pos(1)), "aln_before",
    ).compile()
