from mlclient.xquery import cts


def run():
    return cts.triple_range_query("subject", "predicate", "object").compile()
