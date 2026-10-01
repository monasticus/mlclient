from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_compare_query(
        "system",
        "aln_before",
        "valid",
        options=[fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
