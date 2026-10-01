from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_range_query(
        "valid", "aln_before", options=fn.string(cts.search().index(1)),
    ).compile()
