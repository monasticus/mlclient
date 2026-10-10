from mlclient.xquery import cts, fn


def run():
    return cts.period_range_query(
        "valid",
        "aln_before",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
