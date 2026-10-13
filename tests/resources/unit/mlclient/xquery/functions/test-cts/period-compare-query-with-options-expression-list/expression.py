from mlclient.xquery import cts, fn


def run():
    return cts.period_compare_query(
        "system",
        "aln_before",
        "valid",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
