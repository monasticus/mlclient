from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_compare_query(
        "system", "aln_before", fn.string(cts.search().pos(1)),
    ).compile()
