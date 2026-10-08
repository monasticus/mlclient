from mlclient.xquery import cts


def run():
    return cts.period_compare_query(set(), "aln_before", "valid")
