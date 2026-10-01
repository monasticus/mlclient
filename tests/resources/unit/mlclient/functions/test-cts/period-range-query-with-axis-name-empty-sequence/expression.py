from mlclient.functions.xqy import cts


def run():
    return cts.period_range_query(None, "aln_before").compile()
