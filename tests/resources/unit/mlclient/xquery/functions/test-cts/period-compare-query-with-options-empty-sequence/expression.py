from mlclient.xquery import cts


def run():
    return cts.period_compare_query(
        "system", "aln_before", "valid", options=None,
    ).compile()
