from mlclient.functions.xqy import cts


def run():
    return cts.period_range_query("valid", "aln_before", options="checked").compile()
