from mlclient.functions.xqy import cts


def run():
    return cts.period_compare_query("system", "aln_before", "valid").compile()
