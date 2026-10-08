from mlclient.xquery import cts


def run():
    return cts.period_range_query(set(), "aln_before")
