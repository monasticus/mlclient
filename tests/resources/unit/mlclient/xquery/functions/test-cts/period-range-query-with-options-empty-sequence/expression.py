from mlclient.xquery import cts


def run():
    return cts.period_range_query("valid", "aln_before", options=None).compile()
